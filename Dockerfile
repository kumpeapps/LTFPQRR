FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    build-essential \
    zlib1g-dev \
    nano \
    libffi-dev \
    libjpeg-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Diagnostic: List all files in /app to debug missing app.py issue
RUN echo "=== DIAGNOSTIC: Contents of /app ===" && ls -la /app/
RUN echo "=== DIAGNOSTIC: Looking for app.py specifically ===" && find /app -name "app.py" -type f
RUN echo "=== DIAGNOSTIC: Python version ===" && python --version
# Create upload directory
RUN mkdir -p static/uploads

# Expose port
EXPOSE 5000

# Copy and make startup script executable
COPY start_ltfpqrr.sh /start_ltfpqrr.sh
RUN chmod +x /start_ltfpqrr.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Start the application
CMD ["/start_ltfpqrr.sh"]
