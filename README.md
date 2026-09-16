Helpdesk Ticket System

A lightweight IT helpdesk dashboard that keeps the most urgent ticket on top — automatically. Built with Flask, SQLite, and vanilla JS.

The most pressing ticket is always on top.

Features
Smart priority queue — tickets are ordered by overdue status, then priority, then deadline, then age, so the operator never has to sort manually.
Auto-generated deadlines — if no deadline is given, one is derived from the ticket's priority (URGENT: 2h, HIGH: 8h, NORMAL: 24h, LOW: 72h).
Live overdue detection — computed on every request, not stored, so it's never stale.
Search & filters — by customer name, issue text, priority, status, and assignee, all combinable.
Ticket lifecycle management — OPEN → IN_PROGRESS → RESOLVED → CLOSED, with assignment to support staff.
Dashboard stats — total, active, overdue, urgent, in-progress, and closed ticket counts at a glance.
Tech Stack
Layer	Choice
Backend	Python, Flask
Database	SQLite
Frontend	HTML, CSS, vanilla JavaScript
Runtime	GitHub Codespaces / any Python 3 environment
Project Structure
helpdesk-ticket-system/
├── backend/
│   ├── app.py         # Flask routes, request validation, responses
│   ├── database.py    # SQLite connection + CRUD
│   ├── queue.py        # sort_tickets() / is_overdue() — priority logic
│   └── seed.py         # sample ticket data for local testing
├── static/
│   ├── script.js       # API calls, rendering, interactions
│   └── style.css        # dashboard layout and styling
├── templates/
│   └── index.html      # dashboard markup
├── helpdesk.db          # SQLite database file
├── requirements.txt
├── Procfile
├── README.md
└── REASONING.md         # design decisions and business logic writeup
Getting Started
1. Clone and enter the project
bash
git clone <repo-url>
cd helpdesk-ticket-system
2. Create a virtual environment
bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
3. Install dependencies
bash
pip install -r requirements.txt
4. Run the app
bash
python backend/app.py

The server starts on http://0.0.0.0:5000. Open it in your browser to see the dashboard.

Running in GitHub Codespaces? The dev server binds to 0.0.0.0, so the forwarded port (5000) works out of the box — check the Ports tab.

API Reference
Method	Route	Description
GET	/api/tickets	List tickets. Supports q, priority, status, assigned_to query params
POST	/api/tickets	Create a ticket
GET	/api/tickets/<id>	Get a single ticket
PATCH	/api/tickets/<id>	Update a ticket (partial)
DELETE	/api/tickets/<id>	Delete a ticket
GET	/api/stats	Dashboard statistics
GET	/api/health	Health check

Example — create a ticket:

bash
curl -X POST http://localhost:5000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Rahul Sharma",
    "issue": "Laptop not booting before client demo",
    "priority": "URGENT",
    "assigned_to": "Priya"
  }'

Example — filter the queue:

bash
curl "http://localhost:5000/api/tickets?priority=URGENT&status=OPEN"
Priority & Queue Logic

Tickets are ranked:

Overdue tickets first
Then by priority — URGENT > HIGH > NORMAL > LOW
Then by earliest deadline
Then by oldest ticket

See REASONING.md for the full design rationale.

Deployment

The included Procfile allows the app to run under a production WSGI server (e.g. Gunicorn) on platforms like Render, Railway, or Heroku:

bash
gunicorn backend.app:app

Swap the SQLite file for a managed database (e.g. PostgreSQL) before deploying to handle concurrent writes at scale.

Roadmap
Authentication and role-based access
Email notifications on SLA breach
Pagination for large ticket volumes
Audit log of ticket changes
File attachments per ticket