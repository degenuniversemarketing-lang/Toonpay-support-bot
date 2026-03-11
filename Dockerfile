FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Verify aiogram installation
RUN python -c "import aiogram; print(f'aiogram version: {aiogram.__version__}')"

# Copy source code
COPY src/ ./src/
COPY .env ./

# Run the bot
CMD ["python", "src/bot.py"]
