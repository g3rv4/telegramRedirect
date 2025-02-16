FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=True \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

RUN pip install poetry==2.0.1

COPY *.lock *.toml ./

RUN poetry install --only main --no-root && rm -rf $POETRY_CACHE_DIR

COPY * ./

CMD ["python", "main.py"]
