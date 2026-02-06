# Allowance

A web application for teaching children financial literacy through allowance management. Parents set up accounts with configurable monthly allowances, and children receive daily income, earn interest on savings, and pay penalties on debt.

## How It Works

Rather than giving children a lump sum each month, the app calculates a **daily income** based on the monthly allowance and the number of days in that month. This encourages children to think about money on a daily basis.

- **Positive balances** earn monthly savings interest (default 5% APY), teaching the value of saving.
- **Negative balances** incur monthly penalty interest (default 24% APR), teaching the cost of debt.
- **Withdrawals** require parental approval, adding a layer of intentional spending.

All daily income and interest calculations happen lazily on page load — no cron jobs or schedulers needed. When a child views their dashboard, the app materializes any missing daily income transactions and month-end interest since the last visit.

## Features

- **Two roles**: Parent (admin) and Child accounts
- **Daily income**: Monthly allowance divided by days in the month, accrued daily
- **Savings interest**: Compound interest on positive balances at month-end
- **Debt penalty**: Interest charged on negative balances at month-end
- **Dashboard**: Current balance, recent transactions with running balance, and a 90-day balance history chart
- **Transaction history**: Paginated, filterable by type (income, withdrawal, interest, penalty, adjustment), with running balance
- **Withdrawal requests**: Children submit requests with an optional reason; parents approve or deny
- **Starting balance**: Set an initial balance when creating a child account
- **Backfill support**: Set an allowance start date to retroactively generate income from any past date
- **Notifications**: Optional integration with [ntfy](https://ntfy.sh) to alert parents of new withdrawal requests

## Tech Stack

- **Frontend**: SvelteKit (SPA mode, static adapter) + Pico CSS + Chart.js
- **Backend**: Flask + Flask-SQLAlchemy + Flask-Login
- **Database**: SQLite
- **Deployment**: Docker Compose (single container, multi-stage build)

## Quick Start

```bash
cp .env.example .env
# Edit .env to set your SECRET_KEY and admin credentials
docker compose up --build
```

The app will be available at `http://localhost:5000`.

On first startup, the parent account is created automatically from the `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables.

## Configuration

All configuration is done through environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-this-to-a-random-string` | Flask session secret key |
| `ADMIN_USERNAME` | `parent` | Initial parent account username |
| `ADMIN_PASSWORD` | `changeme` | Initial parent account password |
| `SAVINGS_INTEREST_RATE` | `0.05` | Annual savings interest rate (APY) |
| `CREDIT_INTEREST_RATE` | `0.24` | Annual penalty interest rate (APR) |
| `NTFY_SERVER` | *(empty)* | ntfy server URL (notifications disabled if empty) |
| `NTFY_TOPIC` | `allowance` | ntfy topic for withdrawal request alerts |

## Project Structure

```
allowance/
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── .env.example
├── backend/
│   ├── app.py                  # App factory, blueprint registration, static serving
│   ├── config.py               # Environment-based configuration
│   ├── models.py               # User, Transaction, WithdrawalRequest models
│   ├── seed.py                 # CLI command to create admin account
│   ├── auth.py                 # Login/logout/session endpoints
│   ├── catchup.py              # Lazy daily income + monthly interest engine
│   ├── dashboard.py            # Dashboard endpoint
│   ├── transactions.py         # Paginated transaction history
│   ├── withdrawals.py          # Withdrawal request endpoints
│   ├── admin.py                # Parent admin endpoints
│   ├── notifications.py        # ntfy integration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app.css             # Pico CSS import + minimal overrides
│   │   ├── lib/
│   │   │   ├── api.js          # Fetch wrapper with 401 redirect
│   │   │   ├── stores.js       # User session store
│   │   │   └── utils.js        # formatCurrency, formatDate helpers
│   │   └── routes/
│   │       ├── +layout.svelte  # Nav bar + auth guard
│   │       ├── login/          # Login page
│   │       ├── dashboard/      # Balance, recent transactions, chart
│   │       ├── transactions/   # Full transaction history
│   │       ├── withdraw/       # Withdrawal request form
│   │       └── admin/          # Manage children + approve/deny requests
│   ├── package.json
│   ├── svelte.config.js
│   └── vite.config.js
└── data/                       # SQLite database (Docker volume)
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/login | none | Login with username/password |
| POST | /api/logout | user | End session |
| GET | /api/me | user | Current user info |
| GET | /api/dashboard | child | Balance, recent transactions, 90-day chart data |
| GET | /api/transactions | child | Paginated transactions (`?page=&per_page=&type=`) |
| POST | /api/withdrawals | child | Submit withdrawal request |
| GET | /api/withdrawals | child | List own withdrawal requests |
| GET | /api/admin/users | admin | List children with balances |
| POST | /api/admin/users | admin | Create child account |
| PUT | /api/admin/users/:id | admin | Update child account |
| GET | /api/admin/requests | admin | List withdrawal requests (`?status=pending\|all`) |
| PUT | /api/admin/requests/:id | admin | Approve or deny a request |

## Development

To run the backend and frontend separately for development:

```bash
# Backend
cd backend
pip install -r requirements.txt
flask seed  # Create admin account
flask run

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api` requests to Flask on port 5000.
