const API_URL = "http://127.0.0.1:5000";


// Load everything when page opens
document.addEventListener("DOMContentLoaded", () => {

    loadTransactions();
    loadSummary();
    loadAlerts();

});


// Display messages
function showMessage(message, success = true) {

    const messageElement = document.getElementById("message");

    messageElement.textContent = message;

    messageElement.style.color = success ? "green" : "red";

}


// Convert date for HTML datetime input
function formatDateForInput(date) {

    return date.replace(" ", "T").slice(0, 16);

}


// Convert form date to backend format
function formatDateForAPI(date) {

    return date.replace("T", " ") + ":00";

}


// ------------------------------------
// GET: Load Transactions
// ------------------------------------

async function loadTransactions() {

    try {

        const response = await fetch(`${API_URL}/transactions`);

        if (!response.ok) {
            throw new Error("Unable to load transactions");
        }

        const transactions = await response.json();

        const table = document.getElementById("transactionTable");

        table.innerHTML = "";

        transactions.forEach(transaction => {

            const row = document.createElement("tr");

            const values = [
                transaction.transaction_id,
                transaction.account_id,
                `₹${Number(transaction.amount).toLocaleString("en-IN")}`,
                transaction.transaction_type,
                transaction.channel,
                transaction.region || "-",
                transaction.transaction_datetime
            ];

            values.forEach(value => {

                const cell = document.createElement("td");

                cell.textContent = value;

                row.appendChild(cell);

            });

            const actionCell = document.createElement("td");

            const editButton = document.createElement("button");

            editButton.textContent = "Edit";

            editButton.className = "edit-btn";

            editButton.onclick = () => editTransaction(transaction);

            const deleteButton = document.createElement("button");

            deleteButton.textContent = "Delete";

            deleteButton.className = "delete-btn";

            deleteButton.onclick = () => deleteTransaction(
                transaction.transaction_id
            );

            actionCell.appendChild(editButton);

            actionCell.appendChild(deleteButton);

            row.appendChild(actionCell);

            table.appendChild(row);

        });

    } catch (error) {

        console.error(error);

        showMessage(error.message, false);

    }

}


// ------------------------------------
// POST and PUT: Add or Update
// ------------------------------------

document.getElementById("transactionForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const transactionId = document.getElementById("transactionId").value;

        const transaction = {

            account_id: Number(
                document.getElementById("accountId").value
            ),

            amount: Number(
                document.getElementById("amount").value
            ),

            transaction_datetime: formatDateForAPI(
                document.getElementById("transactionDate").value
            ),

            transaction_type:
                document.getElementById("transactionType").value,

            channel:
                document.getElementById("channel").value,

            region:
                document.getElementById("region").value

        };


        // Choose POST or PUT
        const method = transactionId ? "PUT" : "POST";

        const url = transactionId
            ? `${API_URL}/transactions/${transactionId}`
            : `${API_URL}/transactions`;


        try {

            const response = await fetch(url, {

                method: method,

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(transaction)

            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Operation failed");
            }

            showMessage(data.message, true);

            resetForm();

            await refreshDashboard();

        } catch (error) {

            showMessage(error.message, false);

            console.error(error);

        }

    }
);


// ------------------------------------
// Edit Transaction
// ------------------------------------

function editTransaction(transaction) {

    document.getElementById("transactionId").value =
        transaction.transaction_id;

    document.getElementById("accountId").value =
        transaction.account_id;

    document.getElementById("amount").value =
        transaction.amount;

    document.getElementById("transactionDate").value =
        formatDateForInput(transaction.transaction_datetime);

    document.getElementById("transactionType").value =
        transaction.transaction_type;

    document.getElementById("channel").value =
        transaction.channel;

    document.getElementById("region").value =
        transaction.region || "";

    document.getElementById("formTitle").textContent =
        "Update Transaction";

    document.getElementById("submitButton").textContent =
        "Update Transaction";

    document.getElementById("cancelButton").hidden = false;

    document.getElementById("transaction-form").scrollIntoView({
        behavior: "smooth"
    });

}


// ------------------------------------
// DELETE: Delete Transaction
// ------------------------------------

async function deleteTransaction(transactionId) {

    const confirmed = confirm(
        "Are you sure you want to delete this transaction?"
    );

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `${API_URL}/transactions/${transactionId}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Delete failed");
        }

        showMessage(data.message, true);

        await refreshDashboard();

    } catch (error) {

        showMessage(error.message, false);

        console.error(error);

    }

}


// ------------------------------------
// Reset Form
// ------------------------------------

function resetForm() {

    document.getElementById("transactionForm").reset();

    document.getElementById("transactionId").value = "";

    document.getElementById("formTitle").textContent =
        "Add New Transaction";

    document.getElementById("submitButton").textContent =
        "Add Transaction";

    document.getElementById("cancelButton").hidden = true;

}


// ------------------------------------
// GET: Load Summary
// ------------------------------------

async function loadSummary() {

    try {

        const response = await fetch(`${API_URL}/summary`);

        if (!response.ok) {
            throw new Error("Unable to load summary");
        }

        const data = await response.json();

        document.getElementById("totalTransactions").textContent =
            data.transaction_count;

        document.getElementById("totalAmount").textContent =
            "₹" + Number(data.total_amount).toLocaleString("en-IN");

        document.getElementById("averageAmount").textContent =
            "₹" + Number(data.average_amount).toLocaleString("en-IN", {
                maximumFractionDigits: 2
            });

        document.getElementById("pendingAlerts").textContent =
            data.pending_alerts;

    } catch (error) {

        console.error(error);

    }

}


// ------------------------------------
// GET: Load Fraud Alerts
// ------------------------------------

async function loadAlerts() {

    try {

        const response = await fetch(`${API_URL}/alerts`);

        if (!response.ok) {
            throw new Error("Unable to load alerts");
        }

        const alerts = await response.json();

        const table = document.getElementById("alertTable");

        table.innerHTML = "";

        alerts.forEach(alert => {

            const row = document.createElement("tr");

            const values = [
                alert.alert_id,
                alert.transaction_id,
                `₹${Number(alert.amount).toLocaleString("en-IN")}`,
                alert.risk_score,
                alert.rule_name,
                alert.review_status
            ];

            values.forEach(value => {

                const cell = document.createElement("td");

                cell.textContent = value;

                row.appendChild(cell);

            });

            table.appendChild(row);

        });

    } catch (error) {

        console.error(error);

    }

}


// ------------------------------------
// Refresh Dashboard
// ------------------------------------

async function refreshDashboard() {

    await Promise.all([
        loadTransactions(),
        loadSummary(),
        loadAlerts()
    ]);

    refreshCharts();

}


// Refresh chart images without browser cache
function refreshCharts() {

    document.querySelectorAll(".chart-card img").forEach(img => {

        const baseUrl = img.src.split("?")[0];

        img.src = baseUrl + "?t=" + Date.now();

    });

}