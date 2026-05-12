FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN mkdir -p /app/data /host/var/log

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m pip install --upgrade pip \
    && python -m pip install .

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=3 \
    CMD python -m app.healthcheck

CMD ["python", "-m", "app.main"]
