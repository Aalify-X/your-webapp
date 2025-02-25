# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the required port (Render uses PORT environment variable)
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]  # Change this if your main file is different
