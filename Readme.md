🚀 Lagos Tech Hub - Fullstack Management System
A multi-service architecture combining a Marketplace (Django), HRM System (Node.js/MongoDB), and an Invoice Engine (FastAPI).

🏗️ System Architecture
The project is built using a microservices approach, coordinated via Docker Compose:

Frontend: React (Vite) - Port 5173

Marketplace API: Django + SQLite + Celery - Port 8000

Employee API: Node.js + MongoDB - Port 3000

PDF Service: FastAPI (Invoice/Payslip Generator) - Port 8001

Infrastructure: Redis (Task Broker) & MongoDB (NoSQL Database)

🛠️ Setup & Installation
Prerequisites
Docker & Docker Desktop installed.

Git.

Quick Start
Clone the repository:

Bash
git clone <your-repo-url>
cd market-place
Launch the entire stack:

Bash
docker compose up -d --build
Access the Services:

Frontend: http://localhost:5173

Django Admin: http://localhost:8000/admin

FastAPI Docs: http://localhost:8001/docs

📑 Core Features
🛒 Marketplace
Managed via Django.

Generate PDF receipts for orders via the FastAPI bridge.

Uses Celery for background task processing.

👥 HRM (Employee Management)
Managed via Node.js and MongoDB.

Generate official payslips for employees.

Tracks department, position, and salary details.

🛠️ Troubleshooting
Common Fixes
"Unknown Employee" on PDF: Ensure the django-backend service is running and the ALLOWED_HOSTS in Django includes * or django-backend.

Database Conflicts: If a container name conflict occurs, run:

Bash
docker compose down --remove-orphans
View Logs: To see communication between FastAPI and Django:

Bash
docker compose logs -f fastapi_invoice
🗄️ Data Safety
MongoDB: Data is persisted in the mongo_data Docker volume.

Django: Uses a local db.sqlite3 file. Do not delete this file if you want to keep your marketplace data.