-- HIV Program Activities Tracker Database Schema - PostgreSQL Version
-- =============================================
-- ENUM TYPES
-- =============================================
CREATE TYPE user_role AS ENUM ('accountant', 'admin', 'manager');
CREATE TYPE facility_type AS ENUM ('hospital', 'health_center');
CREATE TYPE planning_status AS ENUM ('draft', 'submitted', 'approved', 'rejected');
CREATE TYPE priority_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE activity_status AS ENUM ('planned', 'ready_to_execute', 'in_progress', 'completed', 'cancelled');
CREATE TYPE execution_status AS ENUM ('started', 'in_progress', 'completed', 'partially_completed');
CREATE TYPE account_category AS ENUM ('asset', 'liability', 'equity', 'revenue', 'expense');
CREATE TYPE transaction_type AS ENUM ('debit', 'credit');
CREATE TYPE audit_action AS ENUM ('CREATE', 'UPDATE', 'DELETE');
CREATE TYPE activity_facility_type AS ENUM ('hospital', 'health_center', 'both');

-- =============================================
-- TRIGGER FUNCTION FOR UPDATED_AT
-- =============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =============================================
-- USER MANAGEMENT TABLES
-- =============================================
-- Users table for authentication and basic info
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    province_id INTEGER NOT NULL,
    district_id INTEGER NOT NULL,
    hospital_id INTEGER NOT NULL,
    role user_role DEFAULT 'accountant',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_province_district ON users (province_id, district_id);

-- Create trigger for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- LOCATION HIERARCHY TABLES
-- =============================================
-- Provinces table
CREATE TABLE provinces (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Districts table
CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    province_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (province_id) REFERENCES provinces(id),
    UNIQUE (province_id, name)
);

CREATE INDEX idx_districts_province ON districts (province_id);

-- =============================================
-- FACILITY MANAGEMENT TABLES
-- =============================================
-- Facilities table (hospitals and health centers)
CREATE TABLE facilities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    facility_type facility_type NOT NULL,
    province_id INTEGER NOT NULL,
    district_id INTEGER NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (province_id) REFERENCES provinces(id),
    FOREIGN KEY (district_id) REFERENCES districts(id)
);

CREATE INDEX idx_facilities_location ON facilities (province_id, district_id);
CREATE INDEX idx_facilities_facility_type ON facilities (facility_type);

-- Create trigger for updated_at
CREATE TRIGGER update_facilities_updated_at
    BEFORE UPDATE ON facilities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- PROGRAM MANAGEMENT TABLES
-- =============================================
-- Programs table (HIV and potentially others)
CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fiscal years table
CREATE TABLE fiscal_years (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE, -- e.g., "2024-2025"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fiscal_years_dates ON fiscal_years (start_date, end_date);

-- =============================================
-- PLANNING TABLES
-- =============================================
-- Planning sessions table
CREATE TABLE planning_sessions (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER NOT NULL,
    program_id INTEGER NOT NULL,
    fiscal_year_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    status planning_status DEFAULT 'draft',
    total_budget DECIMAL(15,2) DEFAULT 0.00,
    submission_date TIMESTAMP NULL,
    approval_date TIMESTAMP NULL,
    approved_by INTEGER NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES facilities(id),
    FOREIGN KEY (program_id) REFERENCES programs(id),
    FOREIGN KEY (fiscal_year_id) REFERENCES fiscal_years(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    UNIQUE (facility_id, program_id, fiscal_year_id)
);

CREATE INDEX idx_planning_sessions_status ON planning_sessions (status);
CREATE INDEX idx_planning_sessions_facility_program ON planning_sessions (facility_id, program_id);

-- Create trigger for updated_at
CREATE TRIGGER update_planning_sessions_updated_at
    BEFORE UPDATE ON planning_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Activity categories table
CREATE TABLE activity_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    facility_type activity_facility_type DEFAULT 'both',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Planned activities table
CREATE TABLE planned_activities (
    id SERIAL PRIMARY KEY,
    planning_session_id INTEGER NOT NULL,
    activity_category_id INTEGER NOT NULL,
    activity_name VARCHAR(255) NOT NULL,
    description TEXT,
    planned_budget DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    planned_start_date DATE,
    planned_end_date DATE,
    target_beneficiaries INTEGER DEFAULT 0,
    success_metrics TEXT,
    priority_level priority_level DEFAULT 'medium',
    status activity_status DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planning_session_id) REFERENCES planning_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (activity_category_id) REFERENCES activity_categories(id)
);

CREATE INDEX idx_planned_activities_planning_session ON planned_activities (planning_session_id);
CREATE INDEX idx_planned_activities_status ON planned_activities (status);
CREATE INDEX idx_planned_activities_dates ON planned_activities (planned_start_date, planned_end_date);

-- Create trigger for updated_at
CREATE TRIGGER update_planned_activities_updated_at
    BEFORE UPDATE ON planned_activities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- EXECUTION TABLES
-- =============================================
-- Activity executions table
CREATE TABLE activity_executions (
    id SERIAL PRIMARY KEY,
    planned_activity_id INTEGER NOT NULL,
    executed_by INTEGER NOT NULL,
    actual_start_date DATE,
    actual_end_date DATE,
    actual_beneficiaries INTEGER DEFAULT 0,
    actual_budget DECIMAL(12,2) DEFAULT 0.00,
    execution_status execution_status DEFAULT 'started',
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    notes TEXT,
    challenges_faced TEXT,
    lessons_learned TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planned_activity_id) REFERENCES planned_activities(id),
    FOREIGN KEY (executed_by) REFERENCES users(id)
);

CREATE INDEX idx_activity_executions_planned_activity ON activity_executions (planned_activity_id);
CREATE INDEX idx_activity_executions_execution_status ON activity_executions (execution_status);
CREATE INDEX idx_activity_executions_dates ON activity_executions (actual_start_date, actual_end_date);

-- Create trigger for updated_at
CREATE TRIGGER update_activity_executions_updated_at
    BEFORE UPDATE ON activity_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- FINANCIAL TABLES
-- =============================================
-- Account types for financial reporting
CREATE TABLE account_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) UNIQUE,
    category account_category NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chart of accounts
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    account_type_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    parent_account_id INTEGER NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_type_id) REFERENCES account_types(id),
    FOREIGN KEY (parent_account_id) REFERENCES accounts(id)
);

CREATE INDEX idx_accounts_account_type ON accounts (account_type_id);
CREATE INDEX idx_accounts_parent ON accounts (parent_account_id);

-- Financial transactions
CREATE TABLE financial_transactions (
    id SERIAL PRIMARY KEY,
    planning_session_id INTEGER NULL,
    activity_execution_id INTEGER NULL,
    account_id INTEGER NOT NULL,
    transaction_type transaction_type NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    transaction_date DATE NOT NULL,
    description TEXT,
    reference_number VARCHAR(100),
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planning_session_id) REFERENCES planning_sessions(id),
    FOREIGN KEY (activity_execution_id) REFERENCES activity_executions(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_financial_transactions_transaction_date ON financial_transactions (transaction_date);
CREATE INDEX idx_financial_transactions_account ON financial_transactions (account_id);
CREATE INDEX idx_financial_transactions_planning_session ON financial_transactions (planning_session_id);
CREATE INDEX idx_financial_transactions_activity_execution ON financial_transactions (activity_execution_id);

-- Budget allocations
CREATE TABLE budget_allocations (
    id SERIAL PRIMARY KEY,
    planning_session_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    allocated_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    spent_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    remaining_amount DECIMAL(15,2) GENERATED ALWAYS AS (allocated_amount - spent_amount) STORED,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planning_session_id) REFERENCES planning_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    UNIQUE (planning_session_id, account_id)
);

CREATE INDEX idx_budget_allocations_planning_session ON budget_allocations (planning_session_id);

-- Create trigger for updated_at
CREATE TRIGGER update_budget_allocations_updated_at
    BEFORE UPDATE ON budget_allocations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- AUDIT AND LOGGING TABLES
-- =============================================
-- Activity logs for audit trail
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action audit_action NOT NULL,
    old_values JSONB NULL,
    new_values JSONB NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_activity_logs_user_action ON activity_logs (user_id, action);
CREATE INDEX idx_activity_logs_table_record ON activity_logs (table_name, record_id);
CREATE INDEX idx_activity_logs_created_at ON activity_logs (created_at);

-- =============================================
-- FOREIGN KEY CONSTRAINTS FOR USERS TABLE
-- =============================================
-- Add foreign key constraints for users table
ALTER TABLE users 
    ADD CONSTRAINT fk_users_province FOREIGN KEY (province_id) REFERENCES provinces(id),
    ADD CONSTRAINT fk_users_district FOREIGN KEY (district_id) REFERENCES districts(id),
    ADD CONSTRAINT fk_users_hospital FOREIGN KEY (hospital_id) REFERENCES facilities(id);

-- =============================================
-- SAMPLE DATA INSERTS
-- =============================================
-- Insert sample provinces
INSERT INTO provinces (name, code) VALUES 
    ('Kigali', 'KGL'),
    ('Eastern Province', 'EST'),
    ('Western Province', 'WST'),
    ('Northern Province', 'NTH'),
    ('Southern Province', 'STH');

-- Insert sample program
INSERT INTO programs (name, code, description) VALUES 
    ('HIV Prevention and Treatment', 'HIV', 'Comprehensive HIV prevention, treatment, and care program');

-- Insert sample fiscal year
INSERT INTO fiscal_years (name, start_date, end_date, is_current) VALUES 
    ('2024-2025', '2024-07-01', '2025-06-30', TRUE);

-- Insert sample account types
INSERT INTO account_types (name, code, category) VALUES 
    ('Cash and Bank', 'CASH', 'asset'),
    ('Program Revenue', 'PREV', 'revenue'),
    ('Program Expenses', 'PEXP', 'expense'),
    ('Equipment', 'EQUP', 'asset'),
    ('Supplies', 'SUPP', 'expense');

-- Insert sample activity categories
INSERT INTO activity_categories (name, code, description, facility_type) VALUES 
    ('HIV Testing and Counseling', 'HTC', 'Voluntary HIV testing and counseling services', 'both'),
    ('Treatment and Care', 'TRT', 'Antiretroviral therapy and patient care', 'both'),
    ('Prevention Programs', 'PREV', 'HIV prevention and education programs', 'both'),
    ('Community Outreach', 'OUTREACH', 'Community-based HIV programs', 'health_center'),
    ('Laboratory Services', 'LAB', 'HIV testing and monitoring laboratory services', 'hospital');

-- =============================================
-- USEFUL VIEWS FOR REPORTING
-- =============================================
-- View for facility summary with location info
-- CREATE VIEW facility_summary AS
-- SELECT 
--     f.id,
--     f.name AS facility_name,
--     f.facility_type,
--     d.name AS district_name,
--     p.name AS province_name,
--     f.is_active
-- FROM facilities f
-- JOIN districts d ON f.district_id = d.id
-- JOIN provinces p ON f.province_id = p.id;

-- -- View for planning session summary
-- CREATE VIEW planning_summary AS
-- SELECT 
--     ps.id,
--     f.name AS facility_name,
--     f.facility_type,
--     prog.name AS program_name,
--     fy.name AS fiscal_year,
--     ps.status,
--     ps.total_budget,
--     COUNT(pa.id) AS planned_activities_count,
--     u.full_name AS created_by_name
-- FROM planning_sessions ps
-- JOIN facilities f ON ps.facility_id = f.id
-- JOIN programs prog ON ps.program_id = prog.id
-- JOIN fiscal_years fy ON ps.fiscal_year_id = fy.id
-- JOIN users u ON ps.created_by = u.id
-- LEFT JOIN planned_activities pa ON ps.id = pa.planning_session_id
-- GROUP BY ps.id, f.name, f.facility_type, prog.name, fy.name, ps.status, ps.total_budget, u.full_name;

-- -- View for budget vs actual reporting
-- CREATE VIEW budget_vs_actual AS
-- SELECT 
--     ba.planning_session_id,
--     a.name AS account_name,
--     at.category AS account_category,
--     ba.allocated_amount,
--     ba.spent_amount,
--     ba.remaining_amount,
--     CASE 
--         WHEN ba.allocated_amount > 0 
--         THEN ROUND((ba.spent_amount / ba.allocated_amount) * 100, 2)
--         ELSE 0 
--     END AS utilization_percentage
-- FROM budget_allocations ba
-- JOIN accounts a ON ba.account_id = a.id
-- JOIN account_types at ON a.account_type_id = at.id;