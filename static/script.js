const API = "/api";

let allTickets = [];
let currentView = "dashboard";

const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
    setupNavigation();
    setupFilters();
    setupNewTicket();
});


// ============================================================
// NAVIGATION
// ============================================================

function setupNavigation() {
    const navItems = document.querySelectorAll("[data-view]");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const view = item.dataset.view;

            if (!view) return;

            currentView = view;

            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");

            if (view === "dashboard") {
                showDashboard();
            }

            if (view === "queue") {
                showQueue();
            }

            if (view === "resolved") {
                showResolved();
            }
        });
    });
}


function showDashboard() {
    currentView = "dashboard";

    document.querySelectorAll(".page-section").forEach(section => {
        section.classList.add("hidden");
    });

    const dashboard = $("#dashboardSection");

    if (dashboard) {
        dashboard.classList.remove("hidden");
    }

    loadDashboard();
}


async function showQueue() {
    currentView = "queue";

    document.querySelectorAll(".page-section").forEach(section => {
        section.classList.add("hidden");
    });

    const queue = $("#queueSection");

    if (queue) {
        queue.classList.remove("hidden");
    }

    await loadTickets();
    renderQueue(allTickets);
}


async function showResolved() {
    currentView = "resolved";

    document.querySelectorAll(".page-section").forEach(section => {
        section.classList.add("hidden");
    });

    const resolved = $("#resolvedSection");

    if (resolved) {
        resolved.classList.remove("hidden");
    }

    await loadTickets();

    const resolvedTickets = allTickets.filter(
        ticket =>
            ticket.status === "RESOLVED" ||
            ticket.status === "CLOSED"
    );

    renderResolved(resolvedTickets);
}


// ============================================================
// DASHBOARD
// ============================================================

async function loadDashboard() {
    await loadStats();
    await loadTickets();

    if (currentView === "dashboard") {
        renderDashboardTickets(allTickets);
    }
}


async function loadStats() {
    try {
        const response = await fetch(`${API}/stats`);

        if (!response.ok) {
            throw new Error("Unable to load statistics");
        }

        const stats = await response.json();

        setText("#totalTickets", stats.total);
        setText("#openTickets", stats.open);
        setText("#overdueTickets", stats.overdue);
        setText("#urgentTickets", stats.urgent);
        setText("#progressTickets", stats.in_progress);
        setText("#closedTickets", stats.closed);

    } catch (error) {
        console.error(error);
    }
}


// ============================================================
// TICKETS
// ============================================================

async function loadTickets(filters = {}) {
    try {
        const params = new URLSearchParams();

        if (filters.q) {
            params.append("q", filters.q);
        }

        if (filters.priority) {
            params.append("priority", filters.priority);
        }

        if (filters.status) {
            params.append("status", filters.status);
        }

        if (filters.assigned_to) {
            params.append("assigned_to", filters.assigned_to);
        }

        const url = `${API}/tickets?${params.toString()}`;

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Unable to load tickets");
        }

        allTickets = await response.json();

        return allTickets;

    } catch (error) {
        console.error("Ticket loading error:", error);
        showToast("Unable to load tickets", "error");
        return [];
    }
}


// ============================================================
// FILTERS
// ============================================================

function setupFilters() {

    const search = $("#searchInput");
    const priority = $("#priorityFilter");
    const status = $("#statusFilter");
    const assignee = $("#assigneeFilter");
    const refresh = $("#refreshBtn");

    if (search) {
        search.addEventListener("input", applyFilters);
    }

    if (priority) {
        priority.addEventListener("change", applyFilters);
    }

    if (status) {
        status.addEventListener("change", applyFilters);
    }

    if (assignee) {
        assignee.addEventListener("change", applyFilters);
    }

    if (refresh) {
        refresh.addEventListener("click", async () => {
            await loadDashboard();
            showToast("Queue refreshed", "success");
        });
    }
}


async function applyFilters() {

    const filters = {
        q: $("#searchInput")?.value || "",
        priority: $("#priorityFilter")?.value || "",
        status: $("#statusFilter")?.value || "",
        assigned_to: $("#assigneeFilter")?.value || ""
    };

    await loadTickets(filters);

    if (currentView === "dashboard") {
        renderDashboardTickets(allTickets);
    }

    if (currentView === "queue") {
        renderQueue(allTickets);
    }

    if (currentView === "resolved") {
        const resolved = allTickets.filter(
            ticket =>
                ticket.status === "RESOLVED" ||
                ticket.status === "CLOSED"
        );

        renderResolved(resolved);
    }
}


// ============================================================
// DASHBOARD TICKET LIST
// ============================================================

function renderDashboardTickets(tickets) {

    const container = $("#ticketList");

    if (!container) return;

    if (tickets.length === 0) {
        container.innerHTML = emptyState("No tickets found");
        return;
    }

    container.innerHTML = tickets
        .map(ticketCard)
        .join("");

    attachTicketActions(container);
}


// ============================================================
// PRIORITY QUEUE
// ============================================================

function renderQueue(tickets) {

    const container = $("#queueList");

    if (!container) return;

    if (tickets.length === 0) {
        container.innerHTML = emptyState("Queue is empty");
        return;
    }

    container.innerHTML = tickets
        .map(ticketCard)
        .join("");

    attachTicketActions(container);
}


// ============================================================
// RESOLVED
// ============================================================

function renderResolved(tickets) {

    const container = $("#resolvedList");

    if (!container) return;

    if (tickets.length === 0) {
        container.innerHTML = emptyState("No resolved tickets");
        return;
    }

    container.innerHTML = tickets
        .map(ticketCard)
        .join("");

    attachTicketActions(container);
}


// ============================================================
// TICKET CARD
// ============================================================

function ticketCard(ticket) {

    const overdue = ticket.overdue;

    return `
        <div class="ticket-card ${overdue ? "ticket-overdue" : ""}"
             data-ticket-id="${ticket.id}">

            <div class="ticket-main">

                <div class="ticket-top">

                    <span class="ticket-id">
                        #${ticket.id}
                    </span>

                    <span class="priority priority-${ticket.priority.toLowerCase()}">
                        ${ticket.priority}
                    </span>

                    ${
                        overdue
                            ? `<span class="overdue-badge">OVERDUE</span>`
                            : ""
                    }

                </div>

                <h3>
                    ${escapeHTML(ticket.issue)}
                </h3>

                <p class="customer">
                    ${escapeHTML(ticket.customer_name)}
                </p>

                <div class="ticket-meta">

                    <span>
                        Deadline:
                        <strong>
                            ${formatDate(ticket.deadline)}
                        </strong>
                    </span>

                    <span>
                        Assigned:
                        <strong>
                            ${ticket.assigned_to || "Unassigned"}
                        </strong>
                    </span>

                    <span>
                        Status:
                        <strong>
                            ${formatStatus(ticket.status)}
                        </strong>
                    </span>

                </div>

            </div>

            <div class="ticket-actions">

                <button
                    class="action-btn"
                    data-action="assign"
                    data-id="${ticket.id}">
                    Assign
                </button>

                <button
                    class="action-btn"
                    data-action="progress"
                    data-id="${ticket.id}">
                    ${ticket.status === "IN_PROGRESS"
                        ? "Mark Open"
                        : "Start"}
                </button>

                <button
                    class="action-btn success"
                    data-action="resolve"
                    data-id="${ticket.id}">
                    Resolve
                </button>

                <button
                    class="action-btn danger"
                    data-action="delete"
                    data-id="${ticket.id}">
                    Delete
                </button>

            </div>

        </div>
    `;
}


// ============================================================
// ACTION BUTTONS
// ============================================================

function attachTicketActions(container) {

    container.querySelectorAll("[data-action]")
        .forEach(button => {

            button.addEventListener("click", async () => {

                const action = button.dataset.action;
                const id = button.dataset.id;

                if (action === "assign") {
                    await assignTicket(id);
                }

                if (action === "progress") {
                    await toggleProgress(id);
                }

                if (action === "resolve") {
                    await resolveTicket(id);
                }

                if (action === "delete") {
                    await deleteTicket(id);
                }

            });

        });
}


// ============================================================
// ASSIGN
// ============================================================

async function assignTicket(id) {

    const person = prompt(
        "Assign ticket to:\n\n1. Priya\n2. Raj"
    );

    if (!person) return;

    let assignedTo = null;

    if (person === "1" || person.toLowerCase() === "priya") {
        assignedTo = "Priya";
    }

    if (person === "2" || person.toLowerCase() === "raj") {
        assignedTo = "Raj";
    }

    if (!assignedTo) {
        showToast("Invalid assignee", "error");
        return;
    }

    await updateTicket(id, {
        assigned_to: assignedTo
    });
}


// ============================================================
// PROGRESS
// ============================================================

async function toggleProgress(id) {

    const ticket = allTickets.find(
        t => String(t.id) === String(id)
    );

    if (!ticket) return;

    const newStatus =
        ticket.status === "IN_PROGRESS"
            ? "OPEN"
            : "IN_PROGRESS";

    await updateTicket(id, {
        status: newStatus
    });
}


// ============================================================
// RESOLVE
// ============================================================

async function resolveTicket(id) {

    const confirmed = confirm(
        "Mark this ticket as RESOLVED?"
    );

    if (!confirmed) return;

    await updateTicket(id, {
        status: "RESOLVED"
    });
}


// ============================================================
// UPDATE API
// ============================================================

async function updateTicket(id, data) {

    try {

        const response = await fetch(
            `${API}/tickets/${id}`,
            {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Update failed");
        }

        showToast(
            "Ticket updated successfully",
            "success"
        );

        await loadDashboard();

        if (currentView === "queue") {
            await showQueue();
        }

        if (currentView === "resolved") {
            await showResolved();
        }

    } catch (error) {

        console.error(error);

        showToast(
            error.message,
            "error"
        );
    }
}


// ============================================================
// DELETE
// ============================================================

async function deleteTicket(id) {

    const confirmed = confirm(
        "Are you sure you want to delete this ticket?"
    );

    if (!confirmed) return;

    try {

        const response = await fetch(
            `${API}/tickets/${id}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Delete failed");
        }

        showToast(
            "Ticket deleted",
            "success"
        );

        await loadDashboard();

        if (currentView === "queue") {
            await showQueue();
        }

        if (currentView === "resolved") {
            await showResolved();
        }

    } catch (error) {

        console.error(error);

        showToast(
            error.message,
            "error"
        );
    }
}


// ============================================================
// NEW TICKET
// ============================================================

function setupNewTicket() {

    const openButton = $("#newTicketBtn");
    const modal = $("#ticketModal");
    const closeButton = $("#closeModal");
    const cancelButton = $("#cancelTicket");
    const form = $("#ticketForm");

    if (openButton) {
        openButton.addEventListener("click", () => {
            openModal();
        });
    }

    if (closeButton) {
        closeButton.addEventListener("click", closeModal);
    }

    if (cancelButton) {
        cancelButton.addEventListener("click", closeModal);
    }

    if (form) {
        form.addEventListener("submit", createNewTicket);
    }

    if (modal) {
        modal.addEventListener("click", event => {

            if (event.target === modal) {
                closeModal();
            }

        });
    }
}


function openModal() {

    const modal = $("#ticketModal");

    if (!modal) return;

    modal.classList.remove("hidden");
}


function closeModal() {

    const modal = $("#ticketModal");
    const form = $("#ticketForm");

    if (modal) {
        modal.classList.add("hidden");
    }

    if (form) {
        form.reset();
    }
}


async function createNewTicket(event) {

    event.preventDefault();

    const customerName = $("#customerName")?.value.trim();
    const issue = $("#issue")?.value.trim();
    const priority = $("#ticketPriority")?.value;
    const deadline = $("#ticketDeadline")?.value;
    const assignedTo = $("#ticketAssignee")?.value;
    const status = $("#ticketStatus")?.value || "OPEN";

    if (!customerName) {
        showToast("Customer name is required", "error");
        return;
    }

    if (!issue) {
        showToast("Issue is required", "error");
        return;
    }

    const payload = {
        customer_name: customerName,
        issue: issue,
        priority: priority || "NORMAL",
        deadline: deadline
            ? new Date(deadline).toISOString().slice(0, 16)
            : "",
        assigned_to: assignedTo || null,
        status: status
    };

    try {

        const response = await fetch(
            `${API}/tickets`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Could not create ticket"
            );
        }

        closeModal();

        showToast(
            `Ticket #${result.id} created successfully`,
            "success"
        );

        await loadDashboard();

    } catch (error) {

        console.error(error);

        showToast(
            error.message,
            "error"
        );
    }
}


// ============================================================
// HELPERS
// ============================================================

function setText(selector, value) {

    const element = $(selector);

    if (element) {
        element.textContent = value;
    }
}


function formatStatus(status) {

    return status
        .replaceAll("_", " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}


function formatDate(dateString) {

    if (!dateString) {
        return "No deadline";
    }

    const date = new Date(dateString);

    if (Number.isNaN(date.getTime())) {
        return dateString;
    }

    return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit"
    });
}


function escapeHTML(value) {

    if (!value) return "";

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function emptyState(message) {

    return `
        <div class="empty-state">
            <div class="empty-icon">✓</div>
            <h3>${message}</h3>
            <p>There are no tickets matching this view.</p>
        </div>
    `;
}


function showToast(message, type = "success") {

    let toast = document.querySelector(".toast");

    if (!toast) {

        toast = document.createElement("div");

        toast.className = "toast";

        document.body.appendChild(toast);
    }

    toast.textContent = message;

    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}