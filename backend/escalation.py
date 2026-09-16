from database import get_all_tickets, update_ticket
from queue import is_overdue, escalate_priority


def run_escalation():
    """
    Check all active tickets.

    If a ticket has breached its deadline,
    increase its priority by exactly one level.

    Example:

    NORMAL -> HIGH
    HIGH -> URGENT
    URGENT -> URGENT

    A closed ticket is never escalated.
    """

    tickets = get_all_tickets()

    escalated_tickets = []

    for ticket in tickets:

        # Closed tickets should never be escalated
        if ticket["status"] == "CLOSED":
            continue

        # Only overdue tickets are eligible
        if not is_overdue(ticket):
            continue

        old_priority = ticket["priority"]
        new_priority = escalate_priority(old_priority)

        # No further escalation possible
        if old_priority == new_priority:
            continue

        updated_ticket = update_ticket(
            ticket["id"],
            {
                "priority": new_priority
            }
        )

        escalated_tickets.append({
            "id": ticket["id"],
            "customer_name": ticket["customer_name"],
            "old_priority": old_priority,
            "new_priority": new_priority
        })

    return escalated_tickets


if __name__ == "__main__":

    result = run_escalation()

    print("\n===================================")
    print("     TICKET ESCALATION CHECK")
    print("===================================\n")

    if not result:
        print("No tickets were escalated.")

    else:
        for ticket in result:
            print(
                f"Ticket #{ticket['id']} | "
                f"{ticket['customer_name']} | "
                f"{ticket['old_priority']} -> "
                f"{ticket['new_priority']}"
            )

    print("\nEscalation check completed.")