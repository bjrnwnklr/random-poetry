#!/bin/bash
source .venv/bin/activate
# run gunicorn, binding to the 5000 port (standard Flask port), i.e. connecting to port 5000 of the app we are running.
exec gunicorn -b :5000 --access-logfile - --error-logfile - app:app