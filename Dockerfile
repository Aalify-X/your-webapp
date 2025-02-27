# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data with error handling
RUN python -c "import nltk; \
    try: \
        nltk.download('punkt', download_dir='/usr/local/share/nltk_data'); \
        nltk.download('wordnet', download_dir='/usr/local/share/nltk_data'); \
    except Exception as e: \
        print(f'NLTK download error: {e}'); \
        exit(1)"

# Copy the rest of the project files
COPY . .

# Use environment variable for port
ENV PORT=5000

# Expose the port
EXPOSE 5000

# Use gunicorn for production with reduced workers
CMD exec gunicorn --workers 2 --threads 2 --bind 0.0.0.0:${PORT} app:app
