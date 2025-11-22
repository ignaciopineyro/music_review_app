#!/bin/bash

echo "🗄️  Starting PostgreSQL only..."

docker-compose up -d db

echo "PostgreSQL started!"
echo "Database: localhost:5432"
echo "User: musicuser"
echo "Password: musicpass"
echo "Database: music_reviews"