# Use a smaller base image
FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 5000
ENV NAME Progrify

# Set the working directory in the container
WORKDIR /app

# Install system dependencies with retry mechanism
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies with reduced memory footprint
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Download NLTK resources
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Install torch with retry mechanism
RUN pip install --no-cache-dir torch==2.6.0 torchvision==0.21.0 --extra-index-url https://download.pytorch.org/whl/cpu

# Expose the port the app runs on
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
