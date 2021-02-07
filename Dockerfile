FROM python:3.8-slim

COPY . /backend
WORKDIR /backend

RUN python3 -m pip install -r requirements.txt
