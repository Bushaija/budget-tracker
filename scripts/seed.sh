#!/bin/bash

# Database seeding script for healthcare planning system
# This script initializes the database with provinces, districts, and facilities

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED_SCRIPT="$SCRIPT_DIR/seed_data.py"
JSON_FILE="$SCRIPT_DIR/province_district_hospitals.json"

# Default database configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5433"}
DB_NAME=${DB_NAME:-"hivtracker"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-"postgres"}

# Export environment variables for Python script
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

print_status "Starting database seeding process..."
print_status "Database: $DB_NAME at $DB_HOST:$DB_PORT"

# Check if required files exist
if [ ! -f "$SEED_SCRIPT" ]; then
    print_error "Seed script not found: $SEED_SCRIPT"
    exit 1
fi

if [ ! -f "$JSON_FILE" ]; then
    print_error "JSON data file not found: $JSON_FILE"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed or not in PATH"
    exit 1
fi

# Check database connectivity
print_status "Testing database connection..."
if ! python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='$DB_HOST',
        port='$DB_PORT',
        dbname='$DB_NAME',
        user='$DB_USER',
        password='$DB_PASSWORD'
    )
    conn.close()
    print('Connection successful')
except Exception as e:
    print(f'Connection failed: {e}')
    exit(1)
" 2>/dev/null; then
    print_error "Cannot connect to database. Please check your database configuration."
    print_warning "Make sure the database is running and credentials are correct."
    exit 1
fi

print_success "Database connection established"

# Run the seeding script
print_status "Running database seeding script..."
if python3 "$SEED_SCRIPT"; then
    print_success "Database seeding completed successfully!"
    print_status "Your database has been initialized with:"
    print_status "- Provinces and districts from Rwanda"
    print_status "- Hospital facilities"
    print_status "- Basic account types and programs"
    print_status "- Default fiscal year"
else
    print_error "Database seeding failed!"
    exit 1
fi

print_success "Seeding process completed!"