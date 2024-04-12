FROM python:3.11-slim

RUN mkdir app
WORKDIR /app

ADD . /app/
ADD .env.docker .env

RUN pip install -r requirements.txt

CMD python main.py

