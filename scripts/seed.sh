#!/usr/bin/env bash

# HIV Program Activities Tracker - Database Seeding Script
# This script seeds the PostgreSQL database with initial data

set -e  # Exit on any error
set -x  # Print commands as they are executed

# Colors for output
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

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/app/core/seeds/initial_data.py"
JSON_DATA_FILE="${SCRIPT_DIR}/app/core/seeds/province_district_hospitals.json"
VERIFY_DATA=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --python-script)
            PYTHON_SCRIPT="$2"
            shift 2
            ;;
        --json-file)
            JSON_DATA_FILE="$2"
            shift 2
            ;;
        --database-url)
            export DATABASE_URL="$2"
            shift 2
            ;;
        --verify)
            VERIFY_DATA=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --python-script PATH    Path to Python seeding script (default: app/core/seeds/initial_data.py)"
            echo "  --json-file PATH        Path to JSON data file (default: app/core/seeds/facilities_data.json)"
            echo "  --database-url URL      PostgreSQL database URL (can also use DATABASE_URL env var)"
            echo "  --verify               Verify seeded data after completion"
            echo "  --help, -h             Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DATABASE_URL           PostgreSQL connection string"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --verify"
            echo "  $0 --json-file /path/to/facilities.json --verify"
            echo "  DATABASE_URL='postgresql://postgres:postgres@localhost:5433/hivtracker' $0"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_status "Starting HIV Program Activities Tracker database seeding..."

# Check if DATABASE_URL is set
if [[ -z "${DATABASE_URL}" ]]; then
    print_error "DATABASE_URL environment variable is not set!"
    print_error "Set it using: export DATABASE_URL='postgresql://postgres:postgres@localhost:5433/hivtracker'"
    print_error "Or pass it as argument: --database-url 'postgresql://postgres:postgres@localhost:5433/hivtracker'"
    exit 1
fi

print_status "Using DATABASE_URL: ${DATABASE_URL//:*@/:***@}"  # Hide password in output

# Check if Python script exists
if [[ ! -f "${PYTHON_SCRIPT}" ]]; then
    print_error "Python script not found: ${PYTHON_SCRIPT}"
    print_error "Make sure the seeding script exists or specify correct path with --python-script"
    exit 1
fi

# Check if JSON data file exists
if [[ ! -f "${JSON_DATA_FILE}" ]]; then
    print_error "JSON data file not found: ${JSON_DATA_FILE}"
    print_error "Make sure the JSON file exists or specify correct path with --json-file"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required Python packages are installed
print_status "Checking Python dependencies..."

if ! python3 -c "import psycopg2" 2>/dev/null; then
    print_warning "psycopg2 not found. Installing..."
    pip3 install psycopg2-binary
fi

if ! python3 -c "import psycopg2" 2>/dev/null; then
    print_error "Failed to install psycopg2. Please install manually:"
    print_error "pip3 install psycopg2-binary"
    exit 1
fi

print_success "Python dependencies are ready"

# Test database connection
print_status "Testing database connection..."

if ! python3 -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
"; then
    print_error "Database connection test failed"
    exit 1
fi

# Create backup timestamp
BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
print_status "Backup timestamp: ${BACKUP_TIMESTAMP}"

# Prepare seeding command
SEED_COMMAND="python3 '${PYTHON_SCRIPT}' --json-file '${JSON_DATA_FILE}'"

if [[ "${VERIFY_DATA}" == true ]]; then
    SEED_COMMAND="${SEED_COMMAND} --verify"
fi

print_status "Executing seeding command..."
print_status "Command: ${SEED_COMMAND}"

# Execute the Python seeding script
if eval "${SEED_COMMAND}"; then
    print_success "Database seeding completed successfully!"
    
    # Show some statistics
    print_status "Getting database statistics..."
    python3 -c "
import psycopg2
import os
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    tables = ['provinces', 'districts', 'facilities']
    print('\n📊 Database Statistics:')
    
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
        count = cursor.fetchone()['count']
        print(f'  {table.capitalize()}: {count} records')
    
    conn.close()
except Exception as e:
    print(f'Could not fetch statistics: {e}')
"
    
    print_success "All operations completed successfully! 🎉"
    
else
    print_error "Database seeding failed!"
    print_error "Check the output above for error details"
    exit 1
fi

# Optional: Run additional post-seeding operations
print_status "Running post-seeding operations..."

# Update table statistics (PostgreSQL)
python3 -c "
import psycopg2
import os

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    
    # Update table statistics for better query performance
    cursor.execute('ANALYZE provinces, districts, facilities;')
    conn.commit()
    conn.close()
    print('✓ Updated table statistics')
except Exception as e:
    print(f'Warning: Could not update statistics: {e}')
"

print_success "Database seeding process completed! ✨"
print_status "Your HIV Program Activities Tracker database is ready to use."