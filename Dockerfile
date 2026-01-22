# build image
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

WORKDIR /app

RUN apt install --upgrade pip

RUN apt-get update && apt-get install -y curl

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt 

COPY . /app

EXPOSE 8000

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]



