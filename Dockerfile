FROM python:3.9

WORKDIR /app_folder

COPY requirements.txt requirements.txt

RUN pip3 install -re requirements.txt

COPY app app

COPY randompoetry randompoetry

COPY .env .

COPY config.py .

COPY setup.py .

COPY data data

CMD [ "python3", "-m", "flask", "run", "--host=0.0.0.0"]