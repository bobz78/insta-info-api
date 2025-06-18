# Use Python base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy app files into container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port (default 5000)
EXPOSE 5000

# Run the app
CMD ["python", "main.py"]