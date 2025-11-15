#!/bin/sh

# This script will run every time the service starts.

# Step 1: Force install the python libraries from requirements.txt
echo "==> Installing requirements..."
pip install --no-cache-dir -r requirements.txt

# Step 2: Run the main python script
echo "==> Starting the MFA checker script..."
python mfa_checker.py
