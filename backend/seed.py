from datetime import datetime, timedelta

from database import (
    get_connection,
    init_db,
    create_ticket
)


def reset_database():

    connection = get_connection()

    connection.execute(
        "DELETE FROM tickets"
    )

    connection.execute(
        "DELETE FROM sqlite_sequence WHERE name='tickets'"
    )

    connection.commit()
    connection.close()


def main():

    init_db()

    reset_database()

    now = datetime.now()

    create_ticket(
        "Rahul Sharma",
        "Laptop won't boot before client demo",
        "URGENT",
        (now - timedelta(minutes=30)).isoformat(timespec="minutes"),
        "Priya",
        "OPEN"
    )

    create_ticket(
        "Aman Gupta",
        "Client demo laptop issue",
        "URGENT",
        (now + timedelta(hours=1)).isoformat(timespec="minutes"),
        None,
        "OPEN"
    )

    create_ticket(
        "Rohit Meena",
        "VPN is not working",
        "HIGH",
        (now + timedelta(hours=3)).isoformat(timespec="minutes"),
        None,
        "OPEN"
    )

    create_ticket(
        "Neha Jain",
        "Need a bigger monitor",
        "NORMAL",
        (now + timedelta(hours=20)).isoformat(timespec="minutes"),
        "Raj",
        "OPEN"
    )

    create_ticket(
        "Karan Singh",
        "Email password reset",
        "LOW",
        (now + timedelta(days=2)).isoformat(timespec="minutes"),
        "Priya",
        "OPEN"
    )

    print("Database seeded successfully.")


if __name__ == "__main__":
    main()