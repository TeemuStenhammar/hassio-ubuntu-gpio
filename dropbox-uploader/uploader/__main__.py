import logging
import argparse
import sys
import os
import time
# Package imports
from uploader import Upload

# Create logger for jplotlib
logger = logging.getLogger(__name__)

def main():
    """Main program.

    Parse command line, then iterate over files and directories under
    rootdir and upload all files.  Skips some temporary files and
    directories, and avoids duplicate uploads by comparing size and
    mtime with the server.
    """

    parser = argparse.ArgumentParser(description='Sync ~/dropbox to Dropbox')
    parser.add_argument('--rootdir',
                        default=os.environ['DROPBOX_ROOTDIR'] if "DROPBOX_ROOTDIR" in os.environ else "~/Downloads",
                        help='Local directory to upload')
    parser.add_argument('--folder', '-f',
                        default=os.environ['DROPBOX_FOLDER'] if "DROPBOX_FOLDER" in os.environ else "",
                        help='Folder name in your Dropbox')
    parser.add_argument('--appKey', default=os.environ['DROPBOX_APP_KEY'] if "DROPBOX_APP_KEY" in os.environ else "",
                        help='Application key')
    parser.add_argument('--appSecret',
                        default=os.environ['DROPBOX_APP_SECRET'] if "DROPBOX_APP_SECRET" in os.environ else "",
                        help='Application secret')
    parser.add_argument('--refreshToken',
                        default=os.environ['DROPBOX_REFRESH_TOKEN'] if "DROPBOX_REFRESH_TOKEN" in os.environ else "",
                        help='Refresh token')
    parser.add_argument('--interval', '-i',
                        default=int(os.environ['DROPBOX_INTERVAL']) if "DROPBOX_INTERVAL" in os.environ else 10,
                        help='Interval to sync from dropbox')
    parser.add_argument('--fromDropbox', action='store_true',
                        help='Direction to synchronize Dropbox')
    parser.add_argument('--fromLocal', action='store_true',
                        help='Direction to synchronize Dropbox')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show all Take default answer on all questions')
    # Parser arguments
    args = parser.parse_args()
    # Initialize loggger
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(name)s - %(levelname)s - %(message)s')
    # Check token
    if not (args.appKey and args.appSecret):
        print(f"app key and app secret must be set")
        sys.exit(2)

    # Check folders
    folder = args.folder
    rootdir = os.path.expanduser(args.rootdir)
    if not os.path.exists(rootdir):
        print(f"{rootdir} does not exist on your filesystem")
        sys.exit(1)
    elif not os.path.isdir(rootdir):
        print(f"{rootdir} is not a folder on your filesystem")
        sys.exit(1)
    # Configure type of overwrite
    if args.fromDropbox:
        overwrite = "dropbox"
    elif args.fromLocal:
        overwrite = "host"
    else:
        overwrite = ""

    # Start sync with refresh token, designed for long living
    upload = Upload(args.appKey, args.appSecret, args.refreshToken, folder, rootdir, interval=args.interval,
                    overwrite=overwrite)

    # Run observer
    logger.info("Server started")
    upload.start()
    # Run loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.debug("Keyboard interrupt")
    # Stop server
    upload.stop()


if __name__ == '__main__':
    main()
