FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements ./requirements

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        --no-cache-dir \
        -r requirements/production.txt

RUN useradd \
    --create-home \
    --uid 10001 \
    --shell /bin/bash \
    appuser

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"]