from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

from database import (
    init_db,
    get_all_tickets,
    get_ticket,
    create_ticket,
    update_ticket,
    delete_ticket
)

from queue import sort_tickets, is_overdue
from escalation import run_escalation


app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

PRIORITIES = {
    "URGENT",
    "HIGH",
    "NORMAL",
    "LOW"
}

STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED"
}

ASSIGNEES = {
    "Priya",
    "Raj"
}


# --------------------------------------------------
# FRONTEND
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# GET ALL TICKETS
# --------------------------------------------------

@app.route("/api/tickets", methods=["GET"])
def tickets():

    # Automatically check overdue tickets
    # and escalate their priority by one level.
    run_escalation()

    # IMPORTANT:
    # This variable must be defined before filtering.
    all_tickets = get_all_tickets()

    filtered = all_tickets

    # Search
    search = request.args.get(
        "q",
        ""
    ).strip().lower()

    if search:

        filtered = [
            ticket
            for ticket in filtered
            if (
                search in ticket["customer_name"].lower()
                or
                search in ticket["issue"].lower()
            )
        ]

    # Priority filter
    priority = request.args.get(
        "priority",
        ""
    ).strip().upper()

    if priority:

        if priority not in PRIORITIES:

            return jsonify({
                "error": "Invalid priority"
            }), 400

        filtered = [
            ticket
            for ticket in filtered
            if ticket["priority"] == priority
        ]

    # Status filter
    status = request.args.get(
        "status",
        ""
    ).strip().upper()

    if status:

        if status not in STATUSES:

            return jsonify({
                "error": "Invalid status"
            }), 400

        filtered = [
            ticket
            for ticket in filtered
            if ticket["status"] == status
        ]

    # Assignee filter
    assigned_to = request.args.get(
        "assigned_to",
        ""
    ).strip()

    if assigned_to:

        if assigned_to not in ASSIGNEES:

            return jsonify({
                "error": "Invalid assignee"
            }), 400

        filtered = [
            ticket
            for ticket in filtered
            if ticket["assigned_to"] == assigned_to
        ]

    # Apply queue ordering
    filtered = sort_tickets(filtered)

    # Add dynamic overdue flag
    for ticket in filtered:

        ticket["overdue"] = is_overdue(ticket)

    return jsonify(filtered)


# --------------------------------------------------
# GET SINGLE TICKET
# --------------------------------------------------

@app.route("/api/tickets/<int:ticket_id>", methods=["GET"])
def get_single_ticket(ticket_id):

    ticket = get_ticket(ticket_id)

    if not ticket:

        return jsonify({
            "error": "Ticket not found"
        }), 404

    ticket["overdue"] = is_overdue(ticket)

    return jsonify(ticket)


# --------------------------------------------------
# CREATE NEW TICKET
# --------------------------------------------------

@app.route("/api/tickets", methods=["POST"])
def add_ticket():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    # Customer name
    customer_name = str(
        data.get("customer_name", "")
    ).strip()

    if not customer_name:

        return jsonify({
            "error": "Customer name is required"
        }), 400

    # Issue
    issue = str(
        data.get("issue", "")
    ).strip()

    if not issue:

        return jsonify({
            "error": "Issue is required"
        }), 400

    # Priority
    priority = str(
        data.get(
            "priority",
            "NORMAL"
        )
    ).strip().upper()

    if priority not in PRIORITIES:

        return jsonify({
            "error": "Invalid priority"
        }), 400

    # Status
    status = str(
        data.get(
            "status",
            "OPEN"
        )
    ).strip().upper()

    if status not in STATUSES:

        return jsonify({
            "error": "Invalid status"
        }), 400

    # Assignee
    assigned_to = data.get(
        "assigned_to"
    )

    if assigned_to:

        assigned_to = str(
            assigned_to
        ).strip()

        if assigned_to not in ASSIGNEES:

            return jsonify({
                "error": "Invalid assignee"
            }), 400

    else:

        assigned_to = None

    # Deadline
    deadline = str(
        data.get(
            "deadline",
            ""
        )
    ).strip()

    # Automatic deadline
    if not deadline:

        hours = (
            2
            if priority == "URGENT"
            else 24
        )

        deadline = (
            datetime.now()
            + timedelta(hours=hours)
        ).isoformat(
            timespec="minutes"
        )

    # Create ticket
    ticket = create_ticket(
        customer_name,
        issue,
        priority,
        deadline,
        assigned_to,
        status
    )

    ticket["overdue"] = is_overdue(ticket)

    return jsonify(ticket), 201


# --------------------------------------------------
# UPDATE TICKET
# --------------------------------------------------

@app.route(
    "/api/tickets/<int:ticket_id>",
    methods=["PATCH"]
)
def edit_ticket(ticket_id):

    existing = get_ticket(ticket_id)

    if not existing:

        return jsonify({
            "error": "Ticket not found"
        }), 404

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    updates = {}

    # Customer name
    if "customer_name" in data:

        customer_name = str(
            data["customer_name"]
        ).strip()

        if not customer_name:

            return jsonify({
                "error": "Customer name cannot be empty"
            }), 400

        updates["customer_name"] = customer_name

    # Issue
    if "issue" in data:

        issue = str(
            data["issue"]
        ).strip()

        if not issue:

            return jsonify({
                "error": "Issue cannot be empty"
            }), 400

        updates["issue"] = issue

    # Priority
    if "priority" in data:

        priority = str(
            data["priority"]
        ).strip().upper()

        if priority not in PRIORITIES:

            return jsonify({
                "error": "Invalid priority"
            }), 400

        updates["priority"] = priority

    # Status
    if "status" in data:

        status = str(
            data["status"]
        ).strip().upper()

        if status not in STATUSES:

            return jsonify({
                "error": "Invalid status"
            }), 400

        updates["status"] = status

    # Assignee
    if "assigned_to" in data:

        assigned_to = data["assigned_to"]

        if assigned_to:

            assigned_to = str(
                assigned_to
            ).strip()

            if assigned_to not in ASSIGNEES:

                return jsonify({
                    "error": "Invalid assignee"
                }), 400

        else:

            assigned_to = None

        updates["assigned_to"] = assigned_to

    # Deadline
    if "deadline" in data:

        deadline = str(
            data["deadline"]
        ).strip()

        if not deadline:

            return jsonify({
                "error": "Deadline cannot be empty"
            }), 400

        updates["deadline"] = deadline

    # Update database
    ticket = update_ticket(
        ticket_id,
        updates
    )

    if not ticket:

        return jsonify({
            "error": "Ticket not found"
        }), 404

    ticket["overdue"] = is_overdue(ticket)

    return jsonify(ticket)


# --------------------------------------------------
# DELETE TICKET
# --------------------------------------------------

@app.route(
    "/api/tickets/<int:ticket_id>",
    methods=["DELETE"]
)
def remove_ticket(ticket_id):

    deleted = delete_ticket(ticket_id)

    if not deleted:

        return jsonify({
            "error": "Ticket not found"
        }), 404

    return jsonify({
        "message": "Ticket deleted successfully"
    })


# --------------------------------------------------
# DASHBOARD STATISTICS
# --------------------------------------------------

@app.route("/api/stats", methods=["GET"])
def stats():

    # Run escalation before calculating statistics
    run_escalation()

    all_tickets = get_all_tickets()

    active_tickets = [
        ticket
        for ticket in all_tickets
        if ticket["status"] != "CLOSED"
    ]

    overdue = sum(
        is_overdue(ticket)
        for ticket in active_tickets
    )

    urgent = sum(
        ticket["priority"] == "URGENT"
        for ticket in active_tickets
    )

    in_progress = sum(
        ticket["status"] == "IN_PROGRESS"
        for ticket in all_tickets
    )

    resolved = sum(
        ticket["status"] == "RESOLVED"
        for ticket in all_tickets
    )

    closed = sum(
        ticket["status"] == "CLOSED"
        for ticket in all_tickets
    )

    return jsonify({

        "total": len(all_tickets),

        "open": len(active_tickets),

        "overdue": overdue,

        "urgent": urgent,

        "in_progress": in_progress,

        "resolved": resolved,

        "closed": closed
    })


# --------------------------------------------------
# MANUAL ESCALATION CHECK
# --------------------------------------------------

@app.route(
    "/api/escalate",
    methods=["POST"]
)
def escalate_tickets():

    escalated = run_escalation()

    return jsonify({

        "message": "Escalation check completed",

        "escalated_count": len(escalated),

        "tickets": escalated
    })


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "ok",
        "message": "Helpdesk API is running"
    })


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    init_db()

    print("")
    print("======================================")
    print("     HELPDESK TICKET SYSTEM")
    print("======================================")
    print("Server running on port 5000")
    print("")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )