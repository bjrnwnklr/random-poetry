FROM python:3.9.1

# create user so we don't run as root, then change into the homedir of the user and switch to the user
# The rest of the dockerfile will now be run under this user.
RUN adduser --disabled-login randompoetry
WORKDIR /home/randompoetry
USER randompoetry

# create a virtual environment and install the requirements into it
COPY docker-requirements.txt requirements.txt
RUN python -m venv .venv
RUN .venv/bin/pip install -r requirements.txt
RUN .venv/bin/pip install gunicorn

# Download nltk cmudict - latest version. Do this after installing python requirements, as nltk is being installed there.
# The -d option specifies the directory to download to. We use /home/randompoetry/nltk_data, as that is the first location
# where nltk looks for the data. If we download without specifying the location, it will be downloaded to /usr/local/share, 
# which is not accessible to the user randompoetry.
RUN .venv/bin/python -m nltk.downloader -d ./nltk_data cmudict

# Copy the app code and make the boot.sh script executable
COPY app app
COPY randompoetry randompoetry
COPY data data
COPY config.py setup.py boot.sh ./

# Expose port 5000 (standard Flask port) and run boot.sh (which activates the virtual environment and runs gunicorn)
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]