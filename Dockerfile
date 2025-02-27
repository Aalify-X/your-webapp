# Use a smaller base image
FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 5000
ENV NAME Progrify

# Use an official Python runtime as a parent image
FROM python:3.9-slim

 8a9d2ddd898b965fd74f41343ab452c2e2ff5db2
# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy the current directory contents into the container at /app
COPY . /app


# Install Python dependencies with reduced memory footprint
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 5000


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK resources
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME Progrify

 8a9d2ddd898b965fd74f41343ab452c2e2ff5db2
# Run app.py when the container launches
CMD ["python", "app.py"]
