from datetime import datetime


PRIORITY_ORDER = {
    "URGENT": 1,
    "HIGH": 2,
    "NORMAL": 3,
    "LOW": 4
}


def parse_datetime(value):
    """
    Convert database datetime string into Python datetime.
    Supports ISO datetime values.
    """
    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(value)


def is_overdue(ticket):
    """
    A ticket is overdue when:
    - it is not CLOSED
    - its deadline has passed
    """

    if ticket["status"] == "CLOSED":
        return False

    try:
        deadline = parse_datetime(ticket["deadline"])
        return datetime.now() > deadline
    except (ValueError, TypeError):
        return False


def sort_tickets(tickets):
    """
    Main queue ordering rule:

    1. Overdue tickets first
    2. Higher priority first
    3. Earlier deadline first
    4. Earlier created ticket first
    """

    def sort_key(ticket):

        overdue_rank = 0 if is_overdue(ticket) else 1

        priority_rank = PRIORITY_ORDER.get(
            ticket["priority"],
            99
        )

        try:
            deadline = parse_datetime(ticket["deadline"])
        except (ValueError, TypeError):
            deadline = datetime.max

        try:
            created_at = parse_datetime(ticket["created_at"])
        except (ValueError, TypeError):
            created_at = datetime.max

        return (
            overdue_rank,
            priority_rank,
            deadline,
            created_at
        )

    return sorted(tickets, key=sort_key)


def escalate_priority(priority):
    """
    Increase priority by exactly ONE level.

    NORMAL -> HIGH
    HIGH   -> URGENT
    URGENT -> URGENT
    LOW    -> LOW
    """

    escalation = {
        "LOW": "LOW",
        "NORMAL": "HIGH",
        "HIGH": "URGENT",
        "URGENT": "URGENT"
    }

    return escalation.get(priority, priority)