# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy all project files into the app directory
COPY . .

# --- SINGLE, MONOLITHIC INSTALLATION STEP ---
# This command chain does everything in one layer to prevent caching issues.
# "set -ex" ensures that the script will exit immediately and print the command if any step fails.
RUN set -ex; \
    \
    # Part 1: Install system dependencies for Google Chrome
    echo "--- Preparing to install system dependencies ---"; \
    apt-get update; \
    apt-get install -y \
        wget \
        gnupg \
        ca-certificates \
        --no-install-recommends; \
    \
    # Part 2: Add the Google Chrome repository and install Chrome
    echo "--- Installing Google Chrome ---"; \
    mkdir -p /etc/apt/keyrings; \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg; \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list; \
    apt-get update; \
    apt-get install -y google-chrome-stable --no-install-recommends; \
    \
    # Part 3: Install Python libraries from requirements.txt
    echo "--- Installing Python libraries ---"; \
    pip install --no-cache-dir -r requirements.txt; \
    \
    # Part 4: Clean up system files
    echo "--- Cleaning up ---"; \
    rm -rf /var/lib/apt/lists/*

# --- FINAL COMMAND WITH DIAGNOSTICS ---
# This command will first print all installed packages to the log, then run the script.
CMD ["sh", "-c", "echo '--- Checking installed packages ---' && pip freeze && echo '--- Starting script ---' && python mfa_checker.py"]