FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN set -ex; \
    echo "--- Preparing to install system dependencies ---"; \
    apt-get update; \
    apt-get install -y \
        wget \
        gnupg \
        ca-certificates \
        --no-install-recommends; \

    echo "--- Installing Google Chrome ---"; \
    mkdir -p /etc/apt/keyrings; \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg; \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list; \
    apt-get update; \
    apt-get install -y google-chrome-stable --no-install-recommends; \

    echo "--- Installing Python libraries ---"; \
    pip install --no-cache-dir -r requirements.txt; \

    echo "--- Cleaning up ---"; \
    rm -rf /var/lib/apt/lists/*

CMD ["python3", "mfa_checker.py"]
