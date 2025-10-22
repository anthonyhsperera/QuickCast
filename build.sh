#!/usr/bin/env bash
# exit on error
set -o errexit

# Install ffmpeg (required for pydub)
apt-get update
apt-get install -y ffmpeg

# Install Python dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create output directory
mkdir -p output

echo "Build completed successfully!"
