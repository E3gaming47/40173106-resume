#!/bin/bash
# Startup script for the backend server

echo "Starting Resume Backend API..."
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting server on http://0.0.0.0:8000"
echo "API Documentation: http://localhost:8000/docs"
python main.py

