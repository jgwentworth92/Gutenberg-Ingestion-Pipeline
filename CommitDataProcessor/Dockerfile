# Use an official lightweight Python image.
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Set the working directory inside the container
WORKDIR /myapp

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements to cache them in Docker layer
COPY ./requirements.txt /myapp/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the rest of your application's code
COPY . .

# Make sure entrypoint script is executable
RUN chmod +x ./entrypoint.sh

# Run the application as a non-root user for security
RUN useradd -m myuser
USER myuser

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]
