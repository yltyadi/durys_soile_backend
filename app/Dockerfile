FROM python:3.9-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY src/ .

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir -r requirements.txt