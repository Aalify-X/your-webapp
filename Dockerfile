FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--workers=1", "--threads=1", "--worker-tmp-dir", "/dev/shm", "--bind", "0.0.0.0:$PORT", "app:app"]
