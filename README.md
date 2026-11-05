# FinGuard – Financial Risk Analysis and Rule-Based Fraud Detection System

## 1. Project Overview

FinGuard is a web-based financial risk analysis and rule-based fraud detection system developed using Python, Flask, MySQL, HTML, CSS, and JavaScript.

The application manages financial transactions, analyzes transaction patterns, calculates risk scores, and identifies potentially suspicious activities using predefined rules.

It provides an interactive dashboard to manage transactions, review fraud alerts, and visualize financial data.

## 2. Project Objectives

- Manage financial transaction records.
- Analyze transaction amounts and patterns.
- Identify potentially suspicious transactions.
- Calculate transaction risk scores.
- Generate alerts for high-risk transactions.
- Perform CRUD operations on transactions.
- Generate financial analysis charts.
- Display financial statistics through a dashboard.

## 3. Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript
- JavaScript Fetch API

### Backend
- Python
- Flask
- MySQL Connector

### Database
- MySQL

### Data Analysis and Visualization
- Pandas
- NumPy
- Matplotlib

### Development Tools
- Visual Studio Code
- MySQL Workbench
- Git
- GitHub

## 4. Main Modules

### Dashboard
Displays financial statistics, transaction information, pending alerts, and analytics.

### Transaction Management
Allows users to add, view, update, and delete financial transactions.

### Risk Assessment
Calculates transaction risk scores using predefined rules.

### Fraud Alert Management
Generates alerts for potentially suspicious transactions and allows their review status to be updated.

### Financial Data Analysis
Uses Python, Pandas, NumPy, and Matplotlib to analyze transactions and generate charts.

## 5. Database Tables

- customers
- accounts
- transactions
- alerts

## 6. Risk Detection Rules

The system uses three predefined rules:

- Transaction amount greater than or equal to ₹50,000: 50 risk points.
- Five or more transactions within one hour, including the current transaction: 30 risk points.
- Transaction region differs from the previous transaction: 20 risk points.

The maximum risk score is 100.

A risk score of 50 or above generates an alert.

These rules are illustrative and are not official banking fraud detection standards.

## 7. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Load dashboard |
| GET | /transactions | View all transactions |
| POST | /transactions | Add transaction |
| PUT | /transactions/<transaction_id> | Update transaction |
| DELETE | /transactions/<transaction_id> | Delete transaction |
| GET | /alerts | View fraud alerts |
| PATCH | /alerts/<alert_id> | Update alert status |
| GET | /summary | Get financial summary |
| GET | /charts/<filename> | Display generated charts |

## 8. Installation and Setup

### Prerequisites

- Python
- MySQL Server
- MySQL Workbench
- Visual Studio Code
- Git

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### Step 2: Open the Project

```bash
cd Financial_fraud_detection
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure MySQL

Execute the following files in MySQL Workbench:

1. schema.sql
2. seed_data.sql

### Step 7: Configure Environment Variables

Create a `.env` file in the project directory.

Add your local MySQL configuration:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=financial_risk_db
```

Do not upload this file to GitHub.

### Step 8: Run the Application

```bash
python app.py
```

Open the dashboard:

http://127.0.0.1:5000

## 9. Analytics

The system generates the following charts:

- Transaction Amount Distribution
- Transactions by Type
- Transaction Risk Score Distribution

Charts are regenerated after successful transaction additions, updates, and deletions.

## 10. Future Enhancements

- Machine learning-based fraud detection.
- Real-time transaction monitoring.
- Email notifications for suspicious transactions.
- Advanced customer behaviour analysis.
- Improved interactive analytics.

## 11. Disclaimer

This is an educational rule-based financial risk analysis project.

The generated risk scores and alerts are illustrative and do not prove that a transaction is fraudulent.