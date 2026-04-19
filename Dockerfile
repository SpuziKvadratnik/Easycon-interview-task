FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    stunnel4 \
    libpq-dev \
    gcc \
    # Save space in the image
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1