#!/usr/bin/env python3
"""
Database seeding script for Healthcare Planning System
Initializes the database with provinces, districts, facilities, and other essential data
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Database seeding class for healthcare planning system"""
    
    def __init__(self, database_url: str = None):
        """Initialize the seeder with database connection"""
        if database_url is None:
            database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.database_url = database_url
        self.conn = None
        self.cur = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def load_json_data(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            file_path = Path(__file__).parent / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} records from {filename}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON data from {filename}: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute a single query"""
        try:
            self.cur.execute(query, params)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def fetch_one(self, query: str, params: tuple = None):
        """Fetch single record"""
        try:
            self.cur.execute(query, params)
            return self.cur.fetchone()
        except Exception as e:
            logger.error(f"Fetch query failed: {e}")
            raise
    
    def record_exists(self, table: str, condition: str, params: tuple) -> bool:
        """Check if a record exists in the table"""
        query = f"SELECT 1 FROM {table} WHERE {condition} LIMIT 1"
        result = self.fetch_one(query, params)
        return result is not None
    
    def seed_provinces(self, facilities_data: List[Dict]) -> Dict[str, int]:
        """Seed provinces table and return province name to ID mapping"""
        logger.info("Seeding provinces...")
        
        # Extract unique provinces from facilities data
        provinces = set()
        for facility in facilities_data:
            provinces.add(facility['province'].lower())
        
        province_mapping = {}
        
        for province_name in sorted(provinces):
            # Check if province already exists
            if not self.record_exists('provinces', 'LOWER(name) = %s', (province_name,)):
                # Insert new province
                query = """
                INSERT INTO provinces (name, code, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                code = province_name[:3].upper()
                params = (
                    province_name.title(),
                    code,
                    f"{province_name.title()} Province",
                    True,
                    datetime.now(),
                    datetime.now()
                )
                self.execute_query(query, params)
                logger.info(f"Inserted province: {province_name.title()}")
            
            # Get province ID
            result = self.fetch_one('SELECT id FROM provinces WHERE LOWER(name) = %s', (province_name,))
            province_mapping[province_name] = result['id']
        
        logger.info(f"Provinces seeding completed. Total: {len(province_mapping)}")
        return province_mapping
    
    def seed_districts(self, facilities_data: List[Dict], province_mapping: Dict[str, int]) -> Dict[str, int]:
        """Seed districts table and return district name to ID mapping"""
        logger.info("Seeding districts...")
        
        # Extract unique districts with their provinces
        districts = {}
        for facility in facilities_data:
            province = facility['province'].lower()
            district = facility['district'].lower()
            districts[district] = province
        
        district_mapping = {}
        
        for district_name, province_name in districts.items():
            province_id = province_mapping[province_name]
            
            # Check if district already exists
            if not self.record_exists('districts', 'LOWER(name) = %s AND province_id = %s', 
                                    (district_name, province_id)):
                # Insert new district
                query = """
                INSERT INTO districts (name, code, province_id, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                code = district_name[:5].upper()
                params = (
                    district_name.title(),
                    code,
                    province_id,
                    f"{district_name.title()} District",
                    True,
                    datetime.now(),
                    datetime.now()
                )
                self.execute_query(query, params)
                logger.info(f"Inserted district: {district_name.title()}")
            
            # Get district ID
            result = self.fetch_one(
                'SELECT id FROM districts WHERE LOWER(name) = %s AND province_id = %s',
                (district_name, province_id)
            )
            district_mapping[district_name] = result['id']
        
        logger.info(f"Districts seeding completed. Total: {len(district_mapping)}")
        return district_mapping
    
    def seed_facilities(self, facilities_data: List[Dict], province_mapping: Dict[str, int], 
                       district_mapping: Dict[str, int]):
        """Seed facilities table"""
        logger.info("Seeding facilities...")
        
        facilities_inserted = 0
        
        for facility_data in facilities_data:
            province_name = facility_data['province'].lower()
            district_name = facility_data['district'].lower()
            facility_name = facility_data['hospital'].lower()
            facility_type = facility_data['facility_type'].upper()
            
            province_id = province_mapping[province_name]
            district_id = district_mapping[district_name]
            
            # Check if facility already exists
            if not self.record_exists(
                'facilities', 
                'LOWER(name) = %s AND district_id = %s AND province_id = %s',
                (facility_name, district_id, province_id)
            ):
                # Insert new facility
                query = """
                INSERT INTO facilities (name, facility_type, province_id, district_id, 
                                     address, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    facility_name.title(),
                    facility_type,
                    province_id,
                    district_id,
                    f"{facility_name.title()}, {district_name.title()}, {province_name.title()}",
                    True,
                    datetime.now(),
                    datetime.now()
                )
                self.execute_query(query, params)
                facilities_inserted += 1
                logger.info(f"Inserted facility: {facility_name.title()}")
        
        logger.info(f"Facilities seeding completed. Inserted: {facilities_inserted}")
    
    def seed_account_types(self):
        """Seed basic account types"""
        logger.info("Seeding account types...")
        
        account_types = [
            ('Cash', 'ASSET', 'CASH', 'Cash and cash equivalents'),
            ('Bank Account', 'ASSET', 'BANK', 'Bank accounts'),
            ('Equipment', 'ASSET', 'EQUIP', 'Medical equipment and assets'),
            ('Supplies', 'ASSET', 'SUPP', 'Medical supplies inventory'),
            ('Accounts Payable', 'LIABILITY', 'AP', 'Amounts owed to suppliers'),
            ('Accrued Expenses', 'LIABILITY', 'ACCR', 'Accrued but unpaid expenses'),
            ('Government Grant', 'REVENUE', 'GRANT', 'Government funding'),
            ('Patient Fees', 'REVENUE', 'FEES', 'Revenue from patient services'),
            ('Salaries', 'EXPENSE', 'SAL', 'Staff salaries and wages'),
            ('Utilities', 'EXPENSE', 'UTIL', 'Electricity, water, internet'),
            ('Medical Supplies', 'EXPENSE', 'MEDSUP', 'Cost of medical supplies'),
            ('Maintenance', 'EXPENSE', 'MAINT', 'Equipment and facility maintenance')
        ]
        
        inserted = 0
        for name, category, code, description in account_types:
            if not self.record_exists('account_types', 'code = %s', (code,)):
                query = """
                INSERT INTO account_types (name, category, code, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """
                params = (name, category, code, True, datetime.now())
                self.execute_query(query, params)
                inserted += 1
        
        logger.info(f"Account types seeding completed. Inserted: {inserted}")
    
    def seed_programs(self):
        """Seed basic programs"""
        logger.info("Seeding programs...")
        
        programs = [
            ('Primary Healthcare', 'PHC', 'Basic healthcare services'),
            ('Maternal Health', 'MAT', 'Maternal and child health services'),
            ('Emergency Care', 'EMR', 'Emergency medical services'),
            ('Preventive Care', 'PREV', 'Preventive healthcare programs'),
            ('Community Health', 'COM', 'Community outreach programs'),
            ('Infrastructure', 'INFRA', 'Facility infrastructure development'),
            ('Training & Education', 'TRAIN', 'Staff training and education programs')
        ]
        
        inserted = 0
        for name, code, description in programs:
            if not self.record_exists('programs', 'code = %s', (code,)):
                query = """
                INSERT INTO programs (name, code, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (name, code, description, True, datetime.now(), datetime.now())
                self.execute_query(query, params)
                inserted += 1
        
        logger.info(f"Programs seeding completed. Inserted: {inserted}")
    
    def seed_fiscal_years(self):
        """Seed fiscal years"""
        logger.info("Seeding fiscal years...")
        
        current_year = datetime.now().year
        fiscal_years = [
            (f'FY {current_year-1}-{current_year}', date(current_year-1, 7, 1), date(current_year, 6, 30), False),
            (f'FY {current_year}-{current_year+1}', date(current_year, 7, 1), date(current_year+1, 6, 30), True),
            (f'FY {current_year+1}-{current_year+2}', date(current_year+1, 7, 1), date(current_year+2, 6, 30), False)
        ]
        
        inserted = 0
        for name, start_date, end_date, is_current in fiscal_years:
            if not self.record_exists('fiscal_years', 'name = %s', (name,)):
                query = """
                INSERT INTO fiscal_years (name, start_date, end_date, is_current, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (name, start_date, end_date, is_current, True, datetime.now(), datetime.now())
                self.execute_query(query, params)
                inserted += 1
        
        logger.info(f"Fiscal years seeding completed. Inserted: {inserted}")
    
    def seed_activity_categories(self):
        """Seed activity categories"""
        logger.info("Seeding activity categories...")
        
        categories = [
            ('Human Immunodeficiency Virus', 'HIV', 't is a virus that attacks the immune system, making it harder for the body to fight off infections and diseases', 'BOTH'),
            ('Tuberculosis', 'TB', 'Tuberculosis is a bacterial infection that primarily affects the lungs', 'BOTH'),
            ('Malaria', 'MAL', 'Malaria is a mosquito-borne disease that can cause fever, chills, and other flu-like symptoms', 'BOTH')
        ]
        
        inserted = 0
        for name, code, description, facility_type in categories:
            if not self.record_exists('activity_categories', 'code = %s', (code,)):
                query = """
                INSERT INTO activity_categories (name, code, description, facility_type, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (name, code, description, facility_type, True, datetime.now(), datetime.now())
                self.execute_query(query, params)
                inserted += 1
        
        logger.info(f"Activity categories seeding completed. Inserted: {inserted}")
    
    def run_seeding(self, json_filename: str = 'province_district_hospitals.json'):
        """Run the complete seeding process"""
        try:
            logger.info("Starting database seeding process...")
            
            # Connect to database
            self.connect()
            
            # Load facility data from JSON
            facilities_data = self.load_json_data(json_filename)
            
            # Seed in order due to foreign key dependencies
            province_mapping = self.seed_provinces(facilities_data)
            district_mapping = self.seed_districts(facilities_data, province_mapping)
            self.seed_facilities(facilities_data, province_mapping, district_mapping)
            
            # Seed other reference data
            self.seed_account_types()
            self.seed_programs()
            self.seed_fiscal_years()
            self.seed_activity_categories()
            
            logger.info("Database seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Seeding process failed: {e}")
            raise
        finally:
            self.disconnect()

    def seed_admin_user(self):
        """Seed an admin user for system access"""
        logger.info("Seeding admin user...")
        
        # Check if admin user already exists
        admin_email = 'admin@healthplanning.rw'
        if self.record_exists('users', 'email = %s', (admin_email,)):
            logger.info("Admin user already exists, skipping...")
            return
        
        # Get the first available province, district, and facility for admin user
        # In a real scenario, you might want to create a special admin facility
        province_result = self.fetch_one('SELECT id FROM provinces WHERE is_active = TRUE LIMIT 1')
        if not province_result:
            logger.error("No active provinces found. Cannot create admin user.")
            return
        
        district_result = self.fetch_one(
            'SELECT id FROM districts WHERE province_id = %s AND is_active = TRUE LIMIT 1',
            (province_result['id'],)
        )
        if not district_result:
            logger.error("No active districts found. Cannot create admin user.")
            return
        
        facility_result = self.fetch_one(
            'SELECT id FROM facilities WHERE province_id = %s AND district_id = %s AND is_active = TRUE LIMIT 1',
            (province_result['id'], district_result['id'])
        )
        if not facility_result:
            logger.error("No active facilities found. Cannot create admin user.")
            return
        
        # Create admin user
        # Note: In production, you should use proper password hashing (bcrypt, scrypt, etc.)
        # This is a placeholder - replace with your actual password hashing mechanism
        import hashlib
        password = 'admin123'  # Default password - should be changed on first login
        password_hash = hashlib.sha256(password.encode()).hexdigest()  # Replace with proper hashing
        
        query = """
        INSERT INTO users (full_name, email, password_hash, province_id, district_id, 
                          facility_id, role, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            'System Administrator',
            admin_email,
            password_hash,
            province_result['id'],
            district_result['id'],
            facility_result['id'],
            'ADMIN',
            True,
            datetime.now(),
            datetime.now()
        )
        
        self.execute_query(query, params)
        logger.info(f"Admin user created successfully with email: {admin_email}")
        logger.warning(f"Default password is '{password}' - CHANGE THIS IMMEDIATELY!")


def main():
    """Main function to run the seeding process"""
    try:
        seeder = DatabaseSeeder()
        seeder.run_seeding()
        print("✅ Database seeding completed successfully!")
        return 0
    except Exception as e:
        print(f"❌ Database seeding failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())