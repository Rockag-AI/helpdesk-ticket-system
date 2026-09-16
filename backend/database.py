import sqlite3
from datetime import datetime


DATABASE = "helpdesk.db"


def get_connection():
    """
    Create and return a connection to the SQLite database.
    """

    connection = sqlite3.connect(DATABASE)

    # Allows us to access columns using column names
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    """
    Create the tickets table if it does not already exist.
    """

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tickets (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_name TEXT NOT NULL,

            issue TEXT NOT NULL,

            priority TEXT NOT NULL
                CHECK(priority IN ('URGENT', 'HIGH', 'NORMAL', 'LOW')),

            deadline TEXT NOT NULL,

            assigned_to TEXT,

            status TEXT NOT NULL
                CHECK(status IN (
                    'OPEN',
                    'IN_PROGRESS',
                    'RESOLVED',
                    'CLOSED'
                )),

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def get_all_tickets():
    """
    Return all tickets from the database.
    """

    connection = get_connection()

    rows = connection.execute("""
        SELECT
            id,
            customer_name,
            issue,
            priority,
            deadline,
            assigned_to,
            status,
            created_at,
            updated_at
        FROM tickets
    """).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_ticket(ticket_id):
    """
    Return a single ticket by ID.
    """

    connection = get_connection()

    row = connection.execute("""
        SELECT
            id,
            customer_name,
            issue,
            priority,
            deadline,
            assigned_to,
            status,
            created_at,
            updated_at
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def create_ticket(
    customer_name,
    issue,
    priority,
    deadline,
    assigned_to,
    status
):
    """
    Create a new ticket.

    created_at and updated_at are both set when
    the ticket is initially created.
    """

    connection = get_connection()

    now = datetime.now().isoformat(
        timespec="minutes"
    )

    cursor = connection.execute("""
        INSERT INTO tickets
        (
            customer_name,
            issue,
            priority,
            deadline,
            assigned_to,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_name,
        issue,
        priority,
        deadline,
        assigned_to,
        status,
        now,
        now
    ))

    connection.commit()

    ticket_id = cursor.lastrowid

    connection.close()

    return get_ticket(ticket_id)


def update_ticket(ticket_id, updates):
    """
    Update an existing ticket.

    Only allowed fields can be modified.
    updated_at is automatically changed.
    """

    allowed_fields = {
        "customer_name",
        "issue",
        "priority",
        "deadline",
        "assigned_to",
        "status"
    }

    # Remove fields that are not allowed
    updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    if not updates:
        return get_ticket(ticket_id)

    connection = get_connection()

    # Automatically update modification time
    updates["updated_at"] = datetime.now().isoformat(
        timespec="minutes"
    )

    fields = ", ".join(
        f"{field} = ?"
        for field in updates.keys()
    )

    values = list(updates.values())

    values.append(ticket_id)

    query = f"""
        UPDATE tickets
        SET {fields}
        WHERE id = ?
    """

    connection.execute(query, values)

    connection.commit()

    connection.close()

    return get_ticket(ticket_id)


def delete_ticket(ticket_id):
    """
    Delete a ticket by ID.

    Returns True if a ticket was deleted.
    Returns False if the ticket did not exist.
    """

    connection = get_connection()

    cursor = connection.execute("""
        DELETE FROM tickets
        WHERE id = ?
    """, (ticket_id,))

    connection.commit()

    deleted = cursor.rowcount > 0

    connection.close()

    return deleted


def clear_all_tickets():
    """
    Delete all tickets.

    This is mainly useful for development/testing.
    """

    connection = get_connection()

    connection.execute("""
        DELETE FROM tickets
    """)

    connection.commit()
    connection.close()


# Initialize database when this file is executed directly
if __name__ == "__main__":

    init_db()

    print("Database initialized successfully.")