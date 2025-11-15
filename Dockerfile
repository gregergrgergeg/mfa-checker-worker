# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for Chrome using the modern key management method
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    --no-install-recommends \
    # Create the keyrings directory
    && mkdir -p /etc/apt/keyrings \
    # Download the Google signing key and save it in the correct location
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    # Add the Google Chrome repository, specifying the signed-by key
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    # Update apt lists and install Chrome
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    # Clean up installation files
    && apt-get purge -y gnupg wget \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Command to run the application when the container launches
CMD ["python", "mfa_checker.py"]
