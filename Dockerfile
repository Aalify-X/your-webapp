# Use a single stage build
FROM python:3.9-slim

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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Download NLTK resources
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Expose the default port
EXPOSE 5000

# Run app.py when the container launches using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
