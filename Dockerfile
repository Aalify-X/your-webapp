# Use a single stage build
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 5000
ENV NAME Progrify
ENV FLASK_ENV production

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Test network connectivity
RUN python -c "import socket; print(socket.gethostbyname('google.com'))"

# Download NLTK resources - create directory first
RUN mkdir -p /usr/local/share/nltk_data
RUN python -c "import nltk; nltk.download('punkt', quiet=True, download_dir='/usr/local/share/nltk_data')"
RUN python -c "import nltk; nltk.download('stopwords', quiet=True, download_dir='/usr/local/share/nltk_data')"

# Set environment variable for NLTK data path
ENV NLTK_DATA=/usr/local/share/nltk_data

# Expose the default port
EXPOSE 5000

# Run app.py when the container launches using gunicorn
CMD ["gunicorn", "--workers=2", "--bind=0.0.0.0:5000", "--timeout=300", "--worker-class=sync", "app:app"]