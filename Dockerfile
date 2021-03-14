FROM python:3.9.1-alpine

RUN adduser -D randompoetry

WORKDIR /home/randompoetry

# create a virtual environment and install the requirements into it
COPY docker-requirements.txt requirements.txt
RUN python -m venv .venv
RUN .venv/bin/pip install -r requirements.txt
RUN .venv/bin/pip install gunicorn

# Download nltk cmudict - latest version. Do this after installing python requirements, as nltk is being installed there.
RUN python -m nltk.downloader cmudict

# Copy the app code and make the boot.sh script executable
COPY app app
COPY randompoetry randompoetry
COPY data data
COPY config.py setup.py boot.sh ./
RUN chmod +x boot.sh

# change owner of the copied files / directories to our new randompoetry user (dirs were created by root)
RUN chown -R randompoetry:randompoetry ./
USER randompoetry

# Expose port 5000 (standard Flask port)
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]