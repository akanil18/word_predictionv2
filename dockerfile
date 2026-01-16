FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1 \
		PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (kept minimal). git is not needed; build tools are often required by some wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# TensorFlow 2.16+ typically requires pip 24+ for some wheels
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all files at once (includes main/, model/, frontend/)
COPY . .

EXPOSE 8000

# Use the correct module path: main.app
CMD ["uvicorn", "main.app:app", "--host", "0.0.0.0", "--port", "8000"]

