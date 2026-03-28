FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Note these env variables will be overriden by docker-compose or can be set at runtime
ENV DB_PATH=/data/videos.db
ENV VIDEO_ROOTS=/videos
ENV HASH_WORKERS=4

ENTRYPOINT ["python", "main.py"]