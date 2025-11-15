# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for Chrome using the modern key management method
# and add "set -e" to ensure the build fails if any command fails.
RUN set -e; \
    apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    --no-install-recommends; \
    mkdir -p /etc/apt/keyrings; \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg; \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list; \
    apt-get update && apt-get install -y google-chrome-stable --no-install-recommends; \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install the Python libraries. "set -e" will make the build fail if this step fails.
RUN set -e; pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# The final, single command to run the application.
# The logic is now inside the Dockerfile itself.
CMD ["python", "mfa_checker.py"]
