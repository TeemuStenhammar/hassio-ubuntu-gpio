import contextlib
import fnmatch
import logging
import os
import re
import shutil
import time
from datetime import datetime
# Functions
from threading import Thread, Event

# Dropbox library
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
# How it is work watchdog
# * https://pythonhosted.org/watchdog/quickstart.html#a-simple-example
# * https://stackoverflow.com/questions/32923451/how-to-run-an-function-when-anything-changes-in-a-dir-with-python-watchdog
# * https://stackoverflow.com/questions/46372041/seeing-multiple-events-with-python-watchdog-library-when-folders-are-created
from watchdog.observers import Observer

# Create logger for jplotlib
logger = logging.getLogger(__name__)
# Chunk size dimension
CHUNK_SIZE = 4 * 1024 * 1024


def get_refresh_token(app_key, app_secret):
    auth_flow = DropboxOAuth2FlowNoRedirect(app_key, app_secret, token_access_type='offline')
    authorize_url = auth_flow.start()
    logger.info("1. Go to: " + authorize_url)
    logger.info("2. Click \"Allow\" (you might have to log in first).")
    logger.info("3. Copy the authorization code.")
    auth_code = input("Enter the authorization code here: ").strip()
    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        print('Error: %s' % (e,))
        exit(1)
    return oauth_result.refresh_token


class Upload(Thread):

    def __init__(self, app_key, app_secret, refresh_token, dbfolder, folder, interval=0.5, overwrite=""):
        Thread.__init__(self)
        self.db_folder = dbfolder
        self.folder = folder
        self.interval = interval
        self.overwrite = overwrite

        if not refresh_token:
            logger.info("Refresh token not set. Calling dropbox API to generate it.")
            refresh_token = get_refresh_token(app_key, app_secret)
            logger.info("Refresh token retreived : '" + refresh_token + "' (keep it for next run)")
        # Load dropbox library
        self.dbx = dropbox.Dropbox(app_key=app_key, app_secret=app_secret, oauth2_refresh_token=refresh_token)
        # Status initialization
        logger.info(f"Dropbox folder name: {dbfolder}")
        logger.debug(f"Local directory: {folder}")

    def run(self):
        while not self.stopped.wait(self.interval):
            logger.debug("Dropbox remote sync")
            # List of all files
            self.syncFromHost(overwrite=False, remove=True)

    def start(self):
        overwrite_db = (self.overwrite == "dropbox")
        overwrite_host = (self.overwrite == "host")
        logger.info(f"Overwrite from Dropbox {overwrite_db}")
        logger.info(f"Overwrite from Host {overwrite_host}")
        # After syncronize from PC
        self.syncFromHost(overwrite=overwrite_host)
        # Load the observer
        self.observer = Observer()
        self.observer.schedule(self, self.folder, recursive=True)
        # Initialize stop event
        self.stopped = Event()
        super().start()
        # Start observer
        self.observer.start()

    def stop(self):
        self.stopped.set()
        self.observer.stop()
        self.observer.join()
        logger.debug("Server stopped")

    def syncFromHost(self, overwrite=False, remove=False):
        logger.info("Start sync from host")
        for dn, dirs, files in os.walk(self.folder):
            # Get local folder
            subfolder = dn[len(self.folder):].strip(os.path.sep)
            logger.debug(f"In folder \"{subfolder}\" ...")
            # include files
            files = [f for f in files if f.endswith(".mkv")]
            # Upload all files and delete after
            for name in list(set(files)):
                fullname = os.path.join(dn, name)
                logger.debug(f"Uploading \"{fullname}\" ...")
                # Upload file
                self.upload(fullname, subfolder, name, overwrite=overwrite)
                # Remove file
                os.remove(fullname)

    def getFolderAndFile(self, src_path):
        abs_path = os.path.dirname(src_path)
        subfolder = os.path.relpath(abs_path, self.folder)
        subfolder = subfolder if subfolder != "." else ""
        name = os.path.basename(src_path)
        return subfolder, name

    def normalizePath(self, subfolder, name):
        """ Normalize folder for Dropbox syncronization.
        """
        path = f"/{self.db_folder}/{subfolder.replace(os.path.sep, '/')}/{name}"
        while '//' in path:
            path = path.replace('//', '/')
        return path

    def upload(self, fullname, subfolder, name, overwrite=False):
        """Upload a file.
            Return the request response, or None in case of error.
        """
        path = self.normalizePath(subfolder, name)
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        mtime = os.path.getmtime(fullname)
        if os.path.isdir(fullname):
            try:
                res = self.dbx.files_create_folder(path)
            except dropbox.exceptions.ApiError as err:
                logger.error(f"API ERROR {err.user_message_text}")
                return None
        else:
            f = open(fullname, 'rb')
            file_size = os.path.getsize(fullname)
            if file_size <= CHUNK_SIZE:
                data = f.read()
                with self.stopwatch(f"upload {file_size} bytes"):
                    try:
                        res = self.dbx.files_upload(data, path, mode,
                                                    client_modified=datetime(*time.gmtime(mtime)[:6]),
                                                    mute=True)
                    except dropbox.exceptions.ApiError as err:
                        logger.error(f"API ERROR {err.user_message_text}")
                        return None
            else:
                upload_session_start_result = self.dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())
                commit = dropbox.files.CommitInfo(path=path)
                # Upload file
                with self.stopwatch(f"upload {file_size} bytes"):
                    while f.tell() < file_size:
                        if ((file_size - f.tell()) <= CHUNK_SIZE):
                            res = self.dbx.files_upload_session_finish(f.read(CHUNK_SIZE), cursor, commit)
                        else:
                            self.dbx.files_upload_session_append(f.read(CHUNK_SIZE), cursor.session_id, cursor.offset)
                            cursor.offset = f.tell()
            # Info data uploaded
            logger.debug(f"uploaded as {res.name.encode('utf8')}")
        return res

    @contextlib.contextmanager
    def stopwatch(self, message):
        """ Context manager to print how long a block of code took.
        """
        t0 = time.time()
        try:
            yield
        finally:
            t1 = time.time()
            logger.debug(f"Total elapsed time for {message}: {(t1 - t0):.3f}")
