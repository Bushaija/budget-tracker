1. Foundation Setup
Start with system essentials and environment setup.
- core/config.py, .env, requirements/
- core/database.py, alembic/, models/base.py
- core/security.py (JWT and password hashing)
- core/deps.py, core/exceptions.py
✅ Get the app running with a minimal main.py and /health endpoint.


🔹 2. Authentication & User Management
These are the gatekeepers of all features.
- Models: user.py
- Schemas: auth.py, user.py
- Services: auth_service.py, user_service.py
- Repositories: user_repository.py
- Endpoints: auth.py, users.py
- Tests: test_auth.py, test_users.py
✅ Enable registration, login, JWT, current user, and admin seeding (scripts/create_admin.py).

🔹 3. Location Hierarchy
- Needed early for user onboarding, planning, and scoping data.
- Models: location.py
- Schemas: location.py
- Services & Repositories: location_service.py, location_repository.py
- Endpoints: locations.py
- Test: test_locations.py
✅ Load seed data for provinces, districts, facilities (scripts/seed_data.py).

🔹 4. User Onboarding Logic
Capture and restrict access until onboarding is complete.
- Extend: user.py, user_service.py
- Add onboarding logic to middleware or service layer
- Block other routes using dependency overrides in api/deps.py

🔹 5. Program & Planning Module
Critical for HIV program design.
- Models: program.py, planning.py
- Schemas: planning.py
- Services: planning_service.py
- Repositories: planning_repository.py
- Endpoints: planning.py
- Tests: test_planning.py

🔹 6. Activity Execution
Track the execution of planned activities.
- Models: execution.py
- Schemas: execution.py
- Services: execution_service.py
- Repositories: execution_repository.py
- Endpoints: execution.py, activities.py
- Tests: test_execution.py

🔹 7. Financial Management
Supports financial tracking and reports.
- Models: financial.py
- Schemas: financial.py
- Services: financial_service.py
- Repositories: financial_repository.py
- Endpoints: financial.py
- Tests: test_financial.py

🔹 8. Reports & Dashboard
Aggregate data for summaries and decision-making.
- Services: report_service.py
- Endpoints: reports.py, dashboard.py
- Schemas: Use common.py
- Tests: test_reports.py

🔹 9. Audit Logging & Admin Tools
Add last-mile improvements, observability, and admin capabilities.
- Models: audit.py
- Services: audit_service.py
- Repositories: audit_repository.py
- Endpoints: admin.py

🔹 10. Middleware, Utilities & Polishing
- Refine UX, security, and maintainability.
- Middleware: cors.py, rate_limiting.py, logging.py, error_handling.py
- Utils: validators.py, formatters.py, constants.py, enums.py, export.py
- Scripts: backup_db.py