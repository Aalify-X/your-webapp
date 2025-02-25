FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only the requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose port for Flask
EXPOSE 5000

# Use waitress to run app on Render
CMD ["python", "app.py"]
