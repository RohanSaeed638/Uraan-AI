# The API image. Build from this folder:  docker build -t uraan-api apps/api
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home app && chown -R app /app
USER app

# Railway, Render and similar set PORT; 8000 otherwise.
ENV PORT=8000
EXPOSE 8000

# RUN_MIGRATIONS=1 applies database migrations before starting (fine for one
# instance; with several, run `alembic upgrade head` as a release step instead).
CMD ["sh", "-c", "if [ \"$RUN_MIGRATIONS\" = \"1\" ]; then alembic upgrade head; fi; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
