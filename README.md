# BizSafi Backend API

> SME Operations + Compliance Assistant for small businesses in Kenya and East Africa.

BizSafi helps salon owners, café operators, and market traders track daily sales, manage stock, and never miss a compliance deadline — all from a simple mobile-first PWA.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (python-jose + passlib PBKDF2) |
| SMS | Africa's Talking |
| AI | Anthropic Claude API |
| Scheduler | APScheduler (daily cron) |

---

## Project Structure

```
bizsafi-backend/
├── app/
│   ├── main.py                  # App entry point, CORS, lifespan, scheduler
│   ├── core/
│   │   ├── config.py            # Typed settings from .env (pydantic-settings)
│   │   ├── database.py          # Engine, SessionLocal, Base, get_db()
│   │   ├── security.py          # JWT create/decode, password hash/verify
│   │   └── deps.py              # get_current_user, get_current_admin dependencies
│   ├── models/
│   │   ├── user.py              # User ORM model
│   │   ├── business.py          # Business ORM model
│   │   ├── sales.py             # Sale ORM model
│   │   ├── stock.py             # StockItem ORM model
│   │   └── reminder.py          # Reminder ORM model
│   ├── schemas/
│   │   ├── user.py              # UserCreate, UserOut, TokenOut
│   │   ├── business.py          # BusinessCreate, BusinessOut
│   │   ├── sales.py             # SaleCreate, SaleOut, SaleSummary
│   │   ├── stock.py             # StockItemCreate, StockItemOut
│   │   └── reminder.py          # ReminderCreate, ReminderOut
│   ├── routes/
│   │   ├── auth.py              # POST /auth/register, /auth/login, GET /auth/me
│   │   ├── business.py          # CRUD /business
│   │   ├── sales.py             # CRUD /sales + summary
│   │   ├── stock.py             # CRUD /stock + low-stock alerts
│   │   └── reminders.py         # CRUD /reminders
│   └── services/
│       ├── ai_service.py        # Claude API integration
│       └── notification_service.py  # Africa's Talking SMS + cron job
├── frontend/                    # Lightweight dashboard UI (HTML/CSS/JS)
├── smoke_test.sh                # End-to-end backend acceptance script
├── .env.example                 # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quick Start (Linux)

### 1. Clone and enter the project

```bash
git clone https://github.com/yourname/bizsafi-backend.git
cd bizsafi-backend
```

### 2. Create a Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update && sudo apt install -y postgresql postgresql-contrib

# Start the service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create the database and user
sudo -u postgres psql <<EOF
CREATE USER bizsafi_user WITH PASSWORD 'yourpassword';
CREATE DATABASE bizsafi_db OWNER bizsafi_user;
GRANT ALL PRIVILEGES ON DATABASE bizsafi_db TO bizsafi_user;
EOF
```

### 5. Configure environment variables

```bash
cp .env.example .env
nano .env   # Fill in your actual values
```

Required values in `.env`:

```env
DATABASE_URL=postgresql://bizsafi_user:yourpassword@localhost:5432/bizsafi_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
AT_USERNAME=sandbox
AT_API_KEY=your_africa_talking_api_key
ANTHROPIC_API_KEY=your_claude_api_key
```

### 6. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API is now running at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/
- **Starter frontend UI:** http://localhost:8000/app

### 7. Run quick backend smoke test

```bash
chmod +x smoke_test.sh
./smoke_test.sh
```

Optional env overrides:

```bash
BASE_URL=http://127.0.0.1:8000 EMAIL=test@example.com PASSWORD='SecurePass123!' ./smoke_test.sh
```

---

## One-Command Setup Script

Save the following as `setup.sh` and run `bash setup.sh`:

```bash
#!/bin/bash
set -e

echo "==> Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Copying .env template..."
cp .env.example .env

echo "==> Generating SECRET_KEY..."
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s/change_this_to_a_long_random_secret_key/$SECRET/" .env

echo ""
echo "✅ Setup complete. Next steps:"
echo "   1. Edit .env with your database and API credentials"
echo "   2. Create the PostgreSQL database (see README)"
echo "   3. Run: source venv/bin/activate && uvicorn app.main:app --reload"
```

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new SME or Admin account |
| POST | `/auth/login` | Login and receive a JWT token |
| POST | `/auth/token` | OAuth2 form login for Swagger Authorize |
| GET | `/auth/me` | Get current user's profile |

### Businesses

| Method | Endpoint | Description |
|---|---|---|
| POST | `/business/` | Register a new business |
| GET | `/business/` | List your businesses |
| GET | `/business/{id}` | Get a single business |
| PATCH | `/business/{id}` | Update business details |
| DELETE | `/business/{id}` | Delete a business (cascades) |

### Sales

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sales/` | Log a sale entry |
| GET | `/sales/?business_id=1` | List sales (with optional date filter) |
| GET | `/sales/summary?business_id=1&period=today` | Revenue summary |
| DELETE | `/sales/{id}` | Delete a sale entry |

### Stock

| Method | Endpoint | Description |
|---|---|---|
| POST | `/stock/` | Add a stock item |
| GET | `/stock/?business_id=1` | List all stock items |
| GET | `/stock/alerts?business_id=1` | Get low-stock alerts |
| GET | `/stock/low?business_id=1` | Low-stock alerts (standard response envelope) |
| PATCH | `/stock/{id}` | Update item (e.g. restock) |
| DELETE | `/stock/{id}` | Remove a stock item |

### Reminders

| Method | Endpoint | Description |
|---|---|---|
| POST | `/reminders/` | Create a reminder |
| GET | `/reminders/?business_id=1` | List reminders (filter by status) |
| PATCH | `/reminders/{id}` | Update or mark as done |
| DELETE | `/reminders/{id}` | Delete a reminder |

### AI Advisory

| Method | Endpoint | Description |
|---|---|---|
| POST | `/ai/query` | Ask Claude for business advice |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard/summary` | Aggregated KPI cards for the authenticated user |

**Example request:**
```json
POST /ai/query
{
  "prompt": "How can a salon in Nairobi track daily profits simply?",
  "business_context": "salon, Westlands Nairobi, 3 staff"
}
```

---

## Authentication Flow

All routes except `/auth/register` and `/auth/login` require a Bearer token:

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","email":"jane@test.com","password":"Secure@123"}'

# 2. Login — copy the access_token from the response
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@test.com","password":"Secure@123"}'

# 3. Use the token
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <your_token_here>"
```

---

## Frontend Starter UI

The project includes a lightweight dashboard at `http://localhost:8000/app`.

### Features

- Register/login/logout with persisted session token
- Create and list businesses
- Select business and add sale/stock/reminder
- Quick sales summary view
- Live activity log for API responses/errors

### Recommended local workflow

1. Start API:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```
2. Open `http://localhost:8000/app`
3. Run acceptance script when needed:
   ```bash
   ./smoke_test.sh
   ```

---

## API Response Conventions

New SaaS-facing endpoints follow a standard envelope:

```json
{
  "success": true,
  "message": "Dashboard summary fetched successfully",
  "data": {}
}
```

Errors follow:

```json
{
  "success": false,
  "message": "Business not found"
}
```

Current envelope endpoints:
- `/dashboard/summary`
- `/stock/low`

---

## Data Model Notes

Core tables include lifecycle timestamps for analytics and auditability:
- `created_at`
- `updated_at`

At startup, the app applies safe additive schema updates for local/dev environments.

---

## SMS Reminder Logic

The daily cron job runs at **08:00 EAT (Nairobi time)** and:
1. Finds all `pending` reminders with `due_date` within 3 days
2. Sends an SMS to the business owner via Africa's Talking
3. Updates the reminder status from `pending` → `sent`

The user marks reminders as `done` manually via `PATCH /reminders/{id}`.

---

## Roadmap (Post-MVP)

- [ ] Add `phone` field to User model for SMS delivery
- [ ] Alembic database migrations
- [ ] Expense tracking module
- [ ] M-Pesa payment integration
- [ ] PDF report generation (monthly summaries)
- [ ] Multi-branch business support
- [ ] WhatsApp notification channel

---

## Contributing

Pull requests are welcome. Please open an issue first for major changes.

---

## License

MIT © BizSafi 2024
