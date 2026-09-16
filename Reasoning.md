Helpdesk Ticket System
1. The Problem

An IT support team receives a constant stream of tickets that are not equally urgent — a laptop that won't boot before a client demo is not the same as a request for a bigger monitor. Each ticket carries a priority and an implicit response-time promise. The one thing the operator must never do is manually scan a flat list to figure out what to work on next.

Core requirement: the ticket that most needs attention is always at the top of the queue, without anyone having to sort it by hand.

2. Priority Model

Four fixed priority levels, enforced server-side as a closed set (PRIORITIES in app.py) so nothing invalid ever reaches the database:

URGENT  >  HIGH  >  NORMAL  >  LOW

Each priority carries an implicit SLA, used to auto-generate a deadline when the operator doesn't supply one:

Priority	Response window
URGENT	2 hours
HIGH	8 hours
NORMAL	24 hours
LOW	72 hours
python
response_hours = {"URGENT": 2, "HIGH": 8, "NORMAL": 24, "LOW": 72}
deadline = (datetime.now() + timedelta(hours=response_hours[priority])).isoformat(timespec="minutes")

This means creating a ticket never requires the operator to think about SLAs — the system commits to a deadline on their behalf, but they can still override it.

3. Overdue Detection

A ticket is overdue the instant "now" passes its stored deadline — this is computed on every read, never written to the database:

overdue = current_time > ticket.deadline

Keeping it dynamic (rather than a stored flag updated by a cron job) means a ticket becomes overdue automatically as time passes, and the field can never drift out of sync with reality. The cost is a small comparison per ticket per request — cheap at this scale, and the right trade-off for correctness over micro-optimization.

4. Queue Ordering — the central business rule

Ordering is not "newest first" or "priority only." It's layered:

Overdue tickets surface first, regardless of priority — a breached promise always outranks an unbroken one.
Among non-overdue tickets, higher priority wins (URGENT → HIGH → NORMAL → LOW).
Earlier deadline breaks ties within the same priority.
Older ticket breaks any remaining tie.

Example:

Ticket	Priority	Deadline	Status
3	HIGH	already passed	OVERDUE
2	URGENT	today	on time
1	NORMAL	tomorrow	on time
4	LOW	tomorrow	on time

Resulting queue: 3 → 2 → 1 → 4. Ticket 3 jumps the priority order entirely because a broken SLA is a stronger signal than an unbroken higher one.

This logic lives in its own module, backend/queue.py (sort_tickets, is_overdue), rather than inline in the route handlers. If the ordering policy changes later, it changes in one place, and it can be unit-tested independently of Flask.

Why the backend decides ordering, not the frontend: the API is the single source of truth. Any client — the current dashboard, a future mobile app, another teammate's script — gets the same order back from GET /api/tickets without re-implementing the rule. overdue is computed and attached to each ticket before the response leaves the server, so no client has to know the current time to render the queue correctly.

5. Data Model & Validation

Fixed, server-validated sets prevent bad data at the boundary rather than catching it downstream:

Priority: URGENT, HIGH, NORMAL, LOW
Status: OPEN → IN_PROGRESS → RESOLVED → CLOSED
Assignee: Priya, Raj, or unassigned

Every write path (POST, PATCH) validates against these sets and returns a 400 with a specific error message on failure — customer_name/issue can't be blank, priority/status/assigned_to must be one of the allowed values. PATCH validates only the fields actually present in the request body, so partial updates don't force the client to resend the whole ticket.

CLOSED and RESOLVED tickets are excluded from "active workload" — they don't count toward overdue/urgent stats or clutter the live queue.

6. API Surface

REST-style, resource-oriented, backed by Flask:

Method	Route	Purpose
GET	/api/tickets	List tickets — supports q, priority, status, assigned_to
POST	/api/tickets	Create a ticket (auto-fills deadline/defaults)
GET	/api/tickets/<id>	Fetch one ticket, 404 if missing
PATCH	/api/tickets/<id>	Partial update, field-level validation
DELETE	/api/tickets/<id>	Remove a ticket
GET	/api/stats	Dashboard counters (total/active/overdue/urgent/in-progress/closed)
GET	/api/health	Liveness check

GET /api/tickets applies filters first (search → priority → status → assignee), then runs the tickets through sort_tickets, so filtering and ordering are independent concerns that compose cleanly — filtering never has to know about ordering and vice versa.

Search matches customer_name and issue case-insensitively via a simple substring check — sufficient at this scale, and it avoids pulling in a full-text search engine for a small ticket volume.

7. Architecture
backend/app.py       Flask routes, request validation, response shaping
backend/database.py  SQLite connection + CRUD, isolated from route logic
backend/queue.py      sort_tickets() / is_overdue() — the one business rule
backend/seed.py       sample data for local testing
templates/index.html  dashboard structure
static/script.js      API calls, rendering, interactions
static/style.css      layout and visual design

Each layer has exactly one reason to change: routes change when the API contract changes, queue.py changes when the priority policy changes, database.py changes when storage changes. This is what makes it realistic to swap SQLite for Postgres later without touching the ordering logic, or to change the SLA policy without touching a single route.

8. Design Decisions
Choice	Why
SQLite	Zero setup, file-based, runs anywhere including Codespaces — right-sized for a prototype, not a production claim.
Flask	Minimal boilerplate for a small REST API + server-rendered shell; fast to iterate on under a time limit.
Vanilla JS, no framework	Keeps the build simple and debuggable without a build step — appropriate given the scope.
Dynamic overdue calc, no stored flag	Correctness by construction beats a background job that can drift or fail silently.
Queue logic isolated in its own module	The one rule most likely to change is the one most worth insulating from the rest of the app.
9. What's Deliberately Out of Scope

This is a working prototype, not a production helpdesk. Left out on purpose, with a clear path to add later given the current separation of concerns:

Auth / role-based permissions
Postgres + indexes + pagination for larger ticket volumes
Email notifications and SLA escalation
Audit log of who changed what
File attachments on tickets
10. Summary

The one rule the whole system is built around:

OVERDUE → URGENT → HIGH → NORMAL → LOW
(deadline, then age, as tie-breakers)

Everything else — validation, filtering, stats, the dashboard — exists to surface that rule correctly and let an operator act on it with the least possible manual scanning.