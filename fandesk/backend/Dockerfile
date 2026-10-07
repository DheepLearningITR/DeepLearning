FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the IPL database into the image (not a volume), so a rebuild always ships fresh data.
COPY scripts/ scripts/
RUN python scripts/load_ipl.py --out /app/ipl/ipl.db

COPY app/ app/

ENV IPL_DB_PATH=/app/ipl/ipl.db \
    APP_DB_PATH=/data/app.db
VOLUME /data
EXPOSE 8000

# Single worker: request state and the SSE queues live in this process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
