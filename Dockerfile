FROM python:3.7-buster

WORKDIR /usr/app/

ENV PYTHONPATH="$PYTHONPATH:/usr/app"

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY src src
COPY config config

ENTRYPOINT ["python3", "-u", "./src/main.py"]
