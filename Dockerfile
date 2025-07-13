FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p static/uploads

# Expose port
EXPOSE 5000

# Copy and make startup script executable
COPY start_ltfpqrr.sh /start_ltfpqrr.sh
RUN chmod +x /start_ltfpqrr.sh

# Set environment variables
ENV PYTHONPATH=/
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Start the application
CMD ["/start_ltfpqrr.sh"]
