# Use Python 3.9 slim image
FROM python:3.9-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create output directory
RUN mkdir -p output

# Copy and make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Use entrypoint script to properly expand PORT variable
CMD ["./start.sh"]
