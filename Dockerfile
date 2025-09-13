FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements ./requirements

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        --no-cache-dir \
        -r requirements/development.txt

RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser

COPY . .

RUN chown -R appuser:appuser /app

USER appuser