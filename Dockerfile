FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Debug: List installed packages
RUN pip list

# Copy source code
COPY src/ ./src/

# Run debug first, then bot
CMD ["sh", "-c", "python src/debug.py && python src/bot.py"]
