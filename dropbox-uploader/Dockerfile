FROM python:3-alpine

# Install requirements
COPY requirements.txt /root
RUN pip install -r /root/requirements.txt
# Define default dropbox folder in docker
ENV DROPBOX_APP_KEY=""
ENV DROPBOX_APP_SECRET=""
ENV DROPBOX_REFRESH_TOKEN=""
ENV DROPBOX_FOLDER="/"
ENV DROPBOX_ROOTDIR="/dropbox"

VOLUME ["/dropbox"]

COPY . /root

WORKDIR "/root"

RUN python setup.py install

ENTRYPOINT ["uploader" ]
