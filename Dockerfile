# Use Python 3.9 as base
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper tiny model during build to avoid timeout at runtime
RUN python -c "import whisper; whisper.load_model('tiny')"

# Copy the rest of the code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs tasks_data tmp

# Use uvicorn directly for better port binding on Railway
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
