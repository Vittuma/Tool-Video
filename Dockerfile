# Use Python 3.9 as base
FROM python:3.9-slim

# Install system dependencies (FFmpeg is required for moviepy/whisper)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

# Command to run the app
CMD ["python", "app.py"]
