#!/bin/bash

echo "Starting Music Review App with Docker..."

docker-compose up --build

echo "Application started"
echo "FastAPI docs available at: http://localhost:8000/docs"
echo "PostgreSQL available at: localhost:5432"