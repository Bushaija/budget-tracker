#!/usr/bin/env python3
"""
PostgreSQL Database seeding script for HIV Program Activities Tracker
Populates provinces, districts, and facilities tables from JSON data
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql, Error
import sys
import os
from typing import List, Dict, Any
import argparse
from urllib.parse import urlparse

class PostgreSQLSeeder:
    def __init__(self, database_url: str = None):
        """Initialize database connection parameters from DATABASE_URL"""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required or pass as parameter")
        
        self.connection = None
        self.cursor = None
        
        # Parse database URL
        self.db_config = self._parse_database_url(self.database_url)
    
    def _parse_database_url(self, url: str) -> dict:
        """Parse PostgreSQL database URL"""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            self.connection.autocommit = False
            print("✓ PostgreSQL database connection established")
            return True
        except Error as e:
            print(f"✗ Error connecting to PostgreSQL database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✓ Database connection closed")
    
    def load_json_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load and parse JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            print(f"✓ Loaded {len(data)} records from {file_path}")
            return data
        except FileNotFoundError:
            print(f"✗ JSON file not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing JSON file: {e}")
            return []
    
    def get_or_create_province(self, province_name: str) -> int:
        """Get existing province ID or create new province"""
        province_name = province_name.strip().title()
        
        # Validate province name against allowed values
        allowed_provinces = {'Kigali', 'Eastern', 'Western', 'Northern', 'Southern'}
        if province_name not in allowed_provinces:
            print(f"  ⚠ Warning: '{province_name}' is not in allowed provinces: {allowed_provinces}")
            # Convert to proper case if it's a known variant
            province_map = {
                'kigali': 'Kigali',
                'eastern': 'Eastern', 
                'western': 'Western',
                'northern': 'Northern',
                'southern': 'Southern'
            }
            province_name = province_map.get(province_name.lower(), province_name)
        
        # Check if province exists
        select_query = "SELECT id FROM provinces WHERE name = %s"
        self.cursor.execute(select_query, (province_name,))
        result = self.cursor.fetchone()
        
        if result:
            return result['id']
        
        # Create new province
        # Generate province code from name (first 3 letters, uppercase)
        province_code = province_name[:3].upper()
        
        insert_query = """
            INSERT INTO provinces (name, code, is_active) 
            VALUES (%s, %s, %s) 
            RETURNING id
        """
        try:
            self.cursor.execute(insert_query, (province_name, province_code, True))
            result = self.cursor.fetchone()
            province_id = result['id']
            print(f"  + Created province: {province_name} (ID: {province_id})")
            return province_id
        except Error as e:
            print(f"  ✗ Error creating province {province_name}: {e}")
            raise
    
    def get_or_create_district(self, district_name: str, province_id: int) -> int:
        """Get existing district ID or create new district"""
        district_name = district_name.strip().title()
        
        # Check if district exists in this province
        select_query = """
            SELECT id FROM districts 
            WHERE name = %s AND province_id = %s
        """
        self.cursor.execute(select_query, (district_name, province_id))
        result = self.cursor.fetchone()
        
        if result:
            return result['id']
        
        # Create new district
        # Generate district code from name (first 3 letters, uppercase)
        district_code = district_name[:3].upper()
        
        insert_query = """
            INSERT INTO districts (province_id, name, code, is_active) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id
        """
        try:
            self.cursor.execute(insert_query, (province_id, district_name, district_code, True))
            result = self.cursor.fetchone()
            district_id = result['id']
            print(f"    + Created district: {district_name} (ID: {district_id})")
            return district_id
        except Error as e:
            print(f"  ✗ Error creating district {district_name}: {e}")
            raise
    
    def get_or_create_facility(self, facility_name: str, facility_type: str, province_id: int, district_id: int) -> int:
        """Get existing facility ID or create new facility"""
        facility_name = facility_name.strip().title()
        facility_type = facility_type.strip().lower()
        
        # Validate facility type
        allowed_types = {'hospital', 'health_center'}
        if facility_type not in allowed_types:
            print(f"  ⚠ Warning: '{facility_type}' is not in allowed types: {allowed_types}. Defaulting to 'hospital'")
            facility_type = 'hospital'
        
        # Check if facility exists in this location
        select_query = """
            SELECT id FROM facilities 
            WHERE name = %s AND province_id = %s AND district_id = %s
        """
        self.cursor.execute(select_query, (facility_name, province_id, district_id))
        result = self.cursor.fetchone()
        
        if result:
            return result['id']
        
        # Create new facility
        insert_query = """
            INSERT INTO facilities (name, facility_type, province_id, district_id, is_active) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING id
        """
        try:
            self.cursor.execute(insert_query, (facility_name, facility_type, province_id, district_id, True))
            result = self.cursor.fetchone()
            facility_id = result['id']
            print(f"      + Created facility: {facility_name} ({facility_type}) (ID: {facility_id})")
            return facility_id
        except Error as e:
            print(f"  ✗ Error creating facility {facility_name}: {e}")
            raise
    
    def seed_initial_data(self):
        """Seed initial required data if not exists"""
        print("\n🌱 Seeding initial required data...")
        
        # Seed programs
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM programs")
            programs_count = self.cursor.fetchone()['count']
            
            if programs_count == 0:
                insert_program = """
                    INSERT INTO programs (name, code, description) 
                    VALUES (%s, %s, %s)
                """
                self.cursor.execute(insert_program, (
                    'HIV Prevention and Treatment',
                    'HIV',
                    'Comprehensive HIV prevention, treatment, and care program'
                ))
                print("  + Created default HIV program")
        except Error as e:
            print(f"  ⚠ Warning: Could not seed programs: {e}")
        
        # Seed fiscal year
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM fiscal_years")
            fy_count = self.cursor.fetchone()['count']
            
            if fy_count == 0:
                insert_fy = """
                    INSERT INTO fiscal_years (name, start_date, end_date, is_current) 
                    VALUES (%s, %s, %s, %s)
                """
                self.cursor.execute(insert_fy, (
                    '2024-2025',
                    '2024-07-01',
                    '2025-06-30',
                    True
                ))
                print("  + Created default fiscal year 2024-2025")
        except Error as e:
            print(f"  ⚠ Warning: Could not seed fiscal years: {e}")
        
        # Seed account types
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM account_types")
            at_count = self.cursor.fetchone()['count']
            
            if at_count == 0:
                account_types = [
                    ('Cash and Bank', 'CASH', 'asset'),
                    ('Program Revenue', 'PREV', 'revenue'),
                    ('Program Expenses', 'PEXP', 'expense'),
                    ('Equipment', 'EQUP', 'asset'),
                    ('Supplies', 'SUPP', 'expense')
                ]
                
                insert_at = """
                    INSERT INTO account_types (name, code, category) 
                    VALUES (%s, %s, %s)
                """
                for name, code, category in account_types:
                    self.cursor.execute(insert_at, (name, code, category))
                
                print(f"  + Created {len(account_types)} account types")
        except Error as e:
            print(f"  ⚠ Warning: Could not seed account types: {e}")
        
        # Seed activity categories
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM activity_categories")
            ac_count = self.cursor.fetchone()['count']
            
            if ac_count == 0:
                activity_categories = [
                    ('HIV Testing and Counseling', 'HTC', 'Voluntary HIV testing and counseling services', 'both'),
                    ('Treatment and Care', 'TRT', 'Antiretroviral therapy and patient care', 'both'),
                    ('Prevention Programs', 'PREV', 'HIV prevention and education programs', 'both'),
                    ('Community Outreach', 'OUTREACH', 'Community-based HIV programs', 'health_center'),
                    ('Laboratory Services', 'LAB', 'HIV testing and monitoring laboratory services', 'hospital')
                ]
                
                insert_ac = """
                    INSERT INTO activity_categories (name, code, description, facility_type) 
                    VALUES (%s, %s, %s, %s)
                """
                for name, code, desc, ftype in activity_categories:
                    self.cursor.execute(insert_ac, (name, code, desc, ftype))
                
                print(f"  + Created {len(activity_categories)} activity categories")
        except Error as e:
            print(f"  ⚠ Warning: Could not seed activity categories: {e}")
    
    def seed_facilities_data(self, json_data: List[Dict[str, Any]]) -> bool:
        """Main seeding function for facilities"""
        if not json_data:
            print("✗ No facility data to seed")
            return False
        
        try:
            print(f"\n🏥 Starting to seed {len(json_data)} facility records...")
            
            for i, record in enumerate(json_data, 1):
                province_name = record.get('province', '').strip()
                district_name = record.get('district', '').strip()
                hospital_name = record.get('hospital', '').strip()
                facility_type = record.get('facility_type', 'hospital').strip()
                
                if not all([province_name, district_name, hospital_name]):
                    print(f"  ⚠ Skipping incomplete record {i}: {record}")
                    continue
                
                print(f"\n[{i}/{len(json_data)}] Processing: {province_name} → {district_name} → {hospital_name} ({facility_type})")
                
                # Create/get province
                province_id = self.get_or_create_province(province_name)
                
                # Create/get district
                district_id = self.get_or_create_district(district_name, province_id)
                
                # Create/get facility
                facility_id = self.get_or_create_facility(hospital_name, facility_type, province_id, district_id)
            
            print(f"\n✓ Successfully processed all facility data!")
            return True
            
        except Exception as e:
            print(f"\n✗ Error during facility seeding: {e}")
            raise
    
    def seed_data(self, json_file_path: str) -> bool:
        """Main seeding orchestrator"""
        try:
            # Load JSON data
            json_data = self.load_json_data(json_file_path)
            if not json_data:
                return False
            
            # Start transaction
            print("\n🚀 Starting database seeding transaction...")
            
            # Seed initial data first
            self.seed_initial_data() 
            
            # Seed facilities data
            success = self.seed_facilities_data(json_data)
            
            if success:
                # Commit all changes
                self.connection.commit()
                print(f"\n✅ Successfully seeded all data and committed transaction!")
                return True
            else:
                self.connection.rollback()
                print(f"\n❌ Seeding failed, transaction rolled back!")
                return False
                
        except Exception as e:
            print(f"\n✗ Error during seeding: {e}")
            self.connection.rollback()
            print("🔄 Transaction rolled back due to error")
            return False
    
    def verify_seeding(self):
        """Verify the seeded data"""
        try:
            # Count records in each table
            tables = [
                'provinces', 'districts', 'facilities', 'programs', 
                'fiscal_years', 'account_types', 'activity_categories'
            ]
            print("\n📊 Seeding verification:")
            
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = self.cursor.fetchone()['count']
                print(f"  {table.replace('_', ' ').title()}: {count} records")
            
            # Show sample facility data
            print("\n📋 Sample facility data preview:")
            query = """
                SELECT p.name as province, d.name as district, 
                       f.name as facility, f.facility_type
                FROM facilities f
                JOIN provinces p ON f.province_id = p.id
                JOIN districts d ON f.district_id = d.id
                ORDER BY p.name, d.name, f.name
                LIMIT 10
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            for row in results:
                print(f"  {row['province']} → {row['district']} → {row['facility']} ({row['facility_type']})")
                
        except Error as e:
            print(f"✗ Error during verification: {e}")

def main():
    parser = argparse.ArgumentParser(description='Seed HIV Program database with facility data')
    parser.add_argument('--database-url', help='PostgreSQL database URL (or set DATABASE_URL env var)')
    parser.add_argument('--json-file', required=True, help='Path to JSON data file')
    parser.add_argument('--verify', action='store_true', help='Verify seeded data after completion')
    
    args = parser.parse_args()
    
    try:
        # Initialize seeder
        seeder = PostgreSQLSeeder(database_url=args.database_url)
        
        # Connect to database
        if not seeder.connect():
            sys.exit(1)
        
        # Seed the data
        if seeder.seed_data(args.json_file):
            print("✅ Seeding completed successfully!")
            
            if args.verify:
                seeder.verify_seeding()
        else:
            print("❌ Seeding failed!")
            sys.exit(1)
    
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
    
    finally:
        if 'seeder' in locals():
            seeder.disconnect()

if __name__ == "__main__":
    main()