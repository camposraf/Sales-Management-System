import sqlite3
import PySimpleGUI as sg
import hashlib

#Layout Setup

CLIENT_LAYOUT = [[sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        # Spacer row
        [sg.Text("", size=(5,5))],

        # First row
        [sg.Text("Client Name:", font=("Helvetica", 20)), sg.Input(key="name", font=("Helvetica", 20), size=(20, 1)),
         sg.Text("Contact:", font=("Helvetica", 20)), sg.Input(key="contact", font=("Helvetica", 20), size=(20,1))],

        # Spacer row
        [sg.Text("", size=(1,1))],

        # Second row
        [sg.Text("Email:", font=("Helvetica", 20)), sg.Input(key="email", font=("Helvetica", 20), size=(20,1)),
         sg.Text("Address:", font=("Helvetica", 20)), sg.Input(key="address", font=("Helvetica", 20), size=(20,1))],

        # Spacer row
        [sg.Text("", size=(1,1))],

        # Buttons row
        [sg.Button("Add Client", font=("Helvetica", 20), size=(12,1)),
         sg.Button("View Clients", font=("Helvetica", 20), size=(12,1)),
         sg.Button("Back", font=("Helvetica", 20), size=(12,1))]]

PROPERTY_LAYOUT = [    [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(5,5))],

        [sg.Text("Client ID", font=("Helvetica", 20)), sg.Input(key="client_id", font=("Helvetica", 20), size=(20, 1)),
        sg.Text("Location", font=("Helvetica", 20)), sg.Input(key="location", font=("Helvetica", 20), size=(20, 1))],

        [sg.Text("", size=(1,1))],

        [sg.Text("Price", font=("Helvetica", 20)), sg.Input(key="price", font=("Helvetica", 20), size=(20, 1)),
        sg.Text("Status", font=("Helvetica", 20)), sg.Input(key="status", font=("Helvetica", 20), size=(20, 1))],

        [sg.Text("", size=(1,1))],

        [sg.Button("Add Payment"), sg.Button("View Properties"), sg.Button("Back")]]

PAYMENTS_LAYOUT = [[sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(5,5))],

        [sg.Text("Client ID", font=("Helvetica", 20)), sg.Input(key="client_id", font=("Helvetica", 20), size=(20, 1)),
         sg.Text("Property ID", font=("Helvetica", 20)), sg.Input(key="property_id", font=("Helvetica", 20), size=(20, 1))],

        [sg.Text("", size=(1,1))],

        [sg.Text("Amount", font=("Helvetica", 20)), sg.Input(key="amount", font=("Helvetica", 20), size=(20, 1)),
         sg.Text("Date (YYYY-MM-DD)", font=("Helvetica", 20)), sg.Input(key="date", font=("Helvetica", 20), size=(20, 1))],

        [sg.Text("", size=(1,1))],

        [sg.Text("Status"), sg.Combo(["Paid", "Pending", "Overdue"], key="status")],

        [sg.Text("", size=(1,1))],

        [sg.Button("Add Payment"), sg.Button("View Payments"), sg.Button("Back")]]

REPORTS_LAYOUT = [[sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
    [sg.Text("", size=(5,5))],

    [sg.Text("Select Report Type:", font=("Helvetica", 20))],
    [sg.Combo(["Overdue Payments", "Payments by Client", "Payments by Property"], key="report_type", font=("Helvetica", 20), size=(20, 1))],

    [sg.Text("", size=(1,1))],

    [sg.Button("Generate Report", font=("Helvetica", 20)), sg.Button("Back", font=("Helvetica", 20))]]

DASHBOARD_LAYOUT = [[sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(5,5))],

        [sg.Button("Manage Clients", font=("Helvetica", 20), size=(20, 1)), sg.Button("Manage Properties", font=("Helvetica", 20), size=(20, 1))],

        [sg.Text("", size=(1,1))],

        [sg.Button("Manage Payments", font=("Helvetica", 20), size=(20, 1)), sg.Button("Reports", font=("Helvetica", 20), size=(20, 1)), sg.Button("Exit", font=("Helvetica", 20), size=(20, 1))]
        ]

LOGIN_LAYOUT = [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(5,5))],

        [sg.Text("Username:", font=("Helvetica", 20)), sg.Input(key="username", font=("Helvetica", 20), size=(20, 1))],
        [sg.Text("Password:", font=("Helvetica", 20)), sg.Input(key="password", password_char="*", font=("Helvetica", 20), size=(20, 1))],

        [sg.Text("", size=(1,1))],

        [sg.Button("Login", font=("Helvetica", 20), size=(20, 1))]
    ]

# Database Setup
def init_db():
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()

    # Employees
    c.execute("""CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT, 
              username TEXT UNIQUE,
              password TEXT,
              role TEXT)""")
    # Clients
    c.execute("""CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              contact TEXT
              email TEXT
              address TEXT)""")
    # Properties
    c.execute("""CREATE TABLE IF NOT EXISTS properties(id INTEGER PRIMARY KEY AUTOINCREMENT,
              client_id INTEGER,
              property_id INTEGER,
              amount REAL,
              date TEXT,
              status TEXT,
              FOREIGN KEY(client_id) REFERENCES clients(id),
              FOREIGN KEY(property_id) REFERENCES properties(id))""")
    # Payments
    c.execute("""CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT,
              client_id INTEGER,
              property_id INTEGER,
              amount REAL,
              status TEXT,
              FOREIGN KEY(client_id) REFERENCES clients(id),
              FOREIGN KEY(property_id) REFERENCES properties(id))""")
    
    conn.commit()
    conn.close()

#Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE username=? AND password=?",
              (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result

# Client Window
def client_window():
    window = sg.Window("Client Management", CLIENT_LAYOUT, resizable=True, element_justification='l')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
         break
    if event == "Add Client":
        conn = sqlite3.connect("primaris.db")
        c = conn.cursor()
        c.execute("""INSERT INTO clients (name, contact, email, address) VALUES (?, ?, ?, ?)""", (values["name"], values["contact"], values["email"], values["address"]))
        conn.commit()
        conn.close()
        sg.popup("Client added successfully!")
    if event == "View Clients":

        conn == sqlite3.connect("primaris.db")
        c = conn.cursor()
        c.execute("SELECT * FROM clients")
        rows = c.fetchall()
        conn.close()
        sg.popup_scrolled("Clients List", *[str(r) for r in rows])

    window.close()

# Property Window
def property_window():
    window = sg.Window("Property Management", PROPERTY_LAYOUT, resizable=True, element_justification='l')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Add Payment":
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            c.execute("""INSERT INTO payments (client_id, property_id, amount, date, status)
                         VALUES (?, ?, ?, ?, ?)""",
                      (values["client_id"], values["property_id"], values["amount"], values["date"], values["status"]))
            conn.commit()
            conn.close()
            sg.popup("Payment recorded successfully!")
        if event == "View Payments":
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            c.execute("SELECT * FROM payments")
            rows = c.fetchall()
            conn.close()
            sg.popup_scrolled("Payments List", *[str(r) for r in rows])

    window.close()

# Payments Window
def payments_window():
    window = sg.Window("Payment Management", PAYMENTS_LAYOUT, resizable=True, element_justification='l')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Add Payment":
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            c.execute("INSERT INTO payments (client_id, property_id, amount, status) VALUES (?, ?, ?, ?)",
                      (values["client_id"], values["property_id"], values["amount"], values["status"]))
            conn.commit()
            conn.close()
            sg.popup("Payment added successfully!")
        if event == "View Payments":
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            c.execute("SELECT * FROM payments")
            rows = c.fetchall()
            conn.close()
            sg.popup_scrolled("Payments List", *[str(r) for r in rows])

    window.close()

#Reports Window
def reports_window():
    window = sg.Window("Reports", REPORTS_LAYOUT, resizable=True, element_justification='l')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Generate Report":
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            report_type = values["report_type"]

            if report_type == "Overdue Payments":
                c.execute("SELECT * FROM payments WHERE status='Overdue'")
                rows = c.fetchall()
                sg.popup_scrolled("Overdue Payments Report", *[str(r) for r in rows])

            elif report_type == "Payments by Client":
                c.execute("""SELECT clients.name, SUM(payments.amount)
                             FROM payments
                             JOIN clients ON payments.client_id = clients.id
                             GROUP BY clients.name""")
                rows = c.fetchall()
                sg.popup_scrolled("Payments by Client", *[f"{r[0]}: ₱{r[1]}" for r in rows])

            elif report_type == "Payments by Property":
                c.execute("""SELECT properties.location, SUM(payments.amount)
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             GROUP BY properties.location""")
                rows = c.fetchall()
                sg.popup_scrolled("Payments by Property", *[f"{r[0]}: ₱{r[1]}" for r in rows])

            conn.close()

    window.close()

# Login Window
def login_window():
    window = sg.Window("Login", LOGIN_LAYOUT, resizable=True, element_justification='c')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED,):
            break
        if event == "Login":
            user = login(values["username"], values["password"])
            if user:
                sg.popup("Login successful!")
                window.close()
                break
            else:
                sg.popup("Invalid username or password. Please try again.")
                
    window.close()

# Dashboard Window
def dashboard():
    window = sg.Window("Sales Management System", DASHBOARD_LAYOUT, resizable=True, element_justification='l')
    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        elif event == "Login":
            login_window()
        elif event == "Manage Clients":
            client_window()
        elif event == "Manage Properties":
            property_window()
        elif event == "Manage Payments":
            payments_window()
        elif event == "Reports":
            reports_window()

    window.close()

# Run the application
if __name__ == "__main__":
    init_db()
    login_window()