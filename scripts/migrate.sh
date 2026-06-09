#!/bin/bash
# Database migration script for WorldCup Forecast Engine 2026
set -e

echo "Running database migrations..."
cd "$(dirname "$0")/../backend"

if [ ! -f alembic.ini ]; then
    echo "Error: alembic.ini not found. Run from project root."
    exit 1
fi

alembic upgrade head
echo "Migrations complete."
