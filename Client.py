import sqlite3
import PySimpleGUI as sg
import hashlib
from datetime import datetime, timedelta
import calendar
import io

#Layout Setup
sg.theme("DarkBlue")

def create_client_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Add Client", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Clients", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Client Name:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="name", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Contact:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="contact", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Email:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="email", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Address:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="address", font=("Helvetica", 20), size=(20,1))],
        ])],
    ]

def create_property_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Add Property", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Properties", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Upload Photo", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Property ID:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="lookup_id", font=("Helvetica", 20), size=(10,1)),
             sg.Button("Lookup", font=("Helvetica", 20))],
            [sg.Text("Name:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="name", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Location:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="location", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Price:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="price", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Status:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="status", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("", size=(1,1))],
            [sg.Image(key="photo_display", size=(240, 240))],
        ])],
    ]

def create_payments_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Add Payment", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Payments", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Setup Plan", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Installments", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Due Payments", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Client ID", font=("Helvetica", 20), size=(18,1)), sg.Input(key="client_id", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Property ID", font=("Helvetica", 20), size=(18,1)), sg.Input(key="property_id", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Amount", font=("Helvetica", 20), size=(18,1)), sg.Input(key="amount", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Date (YYYY-MM-DD)", font=("Helvetica", 20), size=(18,1)), sg.Input(key="date", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Status", font=("Helvetica", 20), size=(18,1)), sg.Combo(["Paid", "Pending", "Overdue"], key="status", font=("Helvetica", 20), size=(12,1))],
        ])],
    ]

def create_reports_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Generate Report", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Select Report Type:", font=("Helvetica", 20), size=(20,1))],
            [sg.Combo(["Overdue Payments", "Payments by Client", "Payments by Property"], key="report_type", font=("Helvetica", 20), size=(25, 1))],
        ])],
    ]

def create_dashboard_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Push(), sg.Button("Manage Clients", font=("Helvetica", 20), size=(20, 1)), sg.Button("Manage Properties", font=("Helvetica", 20), size=(20, 1)), sg.Push()],
        [sg.Text("", size=(1,1))],
        [sg.Push(), sg.Button("Manage Payments", font=("Helvetica", 20), size=(20, 1)), sg.Button("Reports", font=("Helvetica", 20), size=(20, 1)), sg.Push()],
        [sg.Text("", size=(1,1))],
        [sg.Text("", key="due_alert", font=("Helvetica", 16), text_color="red", justification="center")],
        [sg.Text("", size=(1,1))],
        [sg.Push(), sg.Button("Logout", font=("Helvetica", 20), size=(20, 1))]
    ]

def create_login_layout():
    return [
        [sg.Text("Primarius Realty Development", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(5,5))],
        [sg.Text("Username:", font=("Helvetica", 20)), sg.Input(key="username", font=("Helvetica", 20), size=(20, 1))],
        [sg.Text("Password:", font=("Helvetica", 20)), sg.Input(key="password", password_char="*", font=("Helvetica", 20), size=(20, 1))],
        [sg.Text("", size=(1,1))],
        [sg.Button("Login", font=("Helvetica", 20), size=(20, 1))],
        [sg.Button("Register", font=("Helvetica", 20), size=(20, 1))],
        [sg.Button("Exit", font=("Helvetica", 20), size=(20, 1))]
    ]

def create_registration_layout():
    return [
        [sg.Text("Primarius Realty Development", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(5,5))],
        [sg.Text("Username:", font=("Helvetica", 20)), sg.Input(key="username", font=("Helvetica", 20), size=(20, 1))],
        [sg.Text("Password:", font=("Helvetica", 20)), sg.Input(key="password", password_char="*", font=("Helvetica", 20), size=(20, 1))],
        [sg.Text("", size=(1,1))],
        [sg.Button("Register", font=("Helvetica", 20), size=(20, 1))]
    ]

def create_payment_plan_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Calculate", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Create Plan", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Client ID", font=("Helvetica", 20), size=(20,1)), sg.Input(key="client_id", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Property ID", font=("Helvetica", 20), size=(20,1)), sg.Input(key="property_id", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Total Amount", font=("Helvetica", 20), size=(20,1)), sg.Input(key="total_amount", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Down Payment", font=("Helvetica", 20), size=(20,1)), sg.Input(key="down_payment", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Installments", font=("Helvetica", 20), size=(20,1)), sg.Input(key="installments", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Frequency", font=("Helvetica", 20), size=(20,1)), sg.Combo(["Weekly", "Monthly", "Quarterly", "Yearly"], key="frequency", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Start Date (YYYY-MM-DD)", font=("Helvetica", 20), size=(20,1)), sg.Input(key="start_date", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("", size=(1,1))],
            [sg.Text("", key="calc_result", font=("Helvetica", 16), text_color="yellow")],
        ])],
    ]

def create_installments_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Show All Pending", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Check Due Payments", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Mark as Paid", font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Installment ID to pay:", font=("Helvetica", 20), size=(22,1)), sg.Input(key="installment_id", font=("Helvetica", 20), size=(10,1))],
        ])],
    ]

def init_db():
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()

    # Registration
    c.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              first_login INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              role TEXT)""")
    # Clients
    c.execute("""CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT,
              contact TEXT,
              email TEXT,
              address TEXT)""")
    # Properties
    c.execute("PRAGMA table_info(properties)")
    cols = {row[1] for row in c.fetchall()}
    if cols and "name" not in cols:
        c.execute("DROP TABLE IF EXISTS properties")
    c.execute("""CREATE TABLE IF NOT EXISTS properties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT,
        price REAL,
        status TEXT,
        photo BLOB
    )""")
    # Payments
    c.execute("PRAGMA table_info(payments)")
    cols = {row[1] for row in c.fetchall()}
    if cols and "date" not in cols:
        c.execute("DROP TABLE IF EXISTS payments")
    c.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        property_id INTEGER,
        amount REAL,
        date TEXT,
        status TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    # Payment Plans
    c.execute("""CREATE TABLE IF NOT EXISTS payment_plans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        property_id INTEGER,
        total_amount REAL,
        down_payment REAL,
        installment_amount REAL,
        total_installments INTEGER,
        frequency TEXT,
        start_date TEXT,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    # Installments
    c.execute("""CREATE TABLE IF NOT EXISTS payment_installments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER,
        client_id INTEGER,
        property_id INTEGER,
        installment_number INTEGER,
        due_date TEXT,
        amount REAL,
        paid_date TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(plan_id) REFERENCES payment_plans(id),
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    try:
        c.execute("ALTER TABLE properties ADD COLUMN photo BLOB")
    except sqlite3.OperationalError:
        pass
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

def check_due_payments():
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""SELECT pi.id, pi.client_id, pi.installment_number, pi.due_date, pi.amount
                 FROM payment_installments pi
                 WHERE pi.due_date <= ? AND pi.status = 'Pending'""", (today,))
    due = c.fetchall()
    conn.close()
    return due

def create_installments(plan_id, client_id, property_id, total_installments, installment_amount, start_date, frequency):
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()
    start = datetime.strptime(start_date, "%Y-%m-%d")
    for i in range(total_installments):
        if frequency == "Monthly":
            month = start.month + i
            year = start.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            last_day = calendar.monthrange(year, month)[1]
            day = min(start.day, last_day)
            due = datetime(year, month, day)
        elif frequency == "Weekly":
            due = start + timedelta(weeks=i + 1)
        elif frequency == "Quarterly":
            month = start.month + (i * 3)
            year = start.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            last_day = calendar.monthrange(year, month)[1]
            day = min(start.day, last_day)
            due = datetime(year, month, day)
        else:
            due = datetime(start.year + i + 1, start.month, min(start.day, calendar.monthrange(start.year + i + 1, start.month)[1]))
        c.execute("""INSERT INTO payment_installments (plan_id, client_id, property_id, installment_number, due_date, amount, status)
                     VALUES (?, ?, ?, ?, ?, ?, 'Pending')""",
                  (plan_id, client_id, property_id, i + 1, due.strftime("%Y-%m-%d"), installment_amount))
    conn.commit()
    conn.close()

def register_window():
    window = sg.Window("Register", create_registration_layout(), resizable=True, element_justification='c', size=(900, 600))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED,):
            break
        if event == "Register":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            try:
                c.execute("INSERT INTO employees (username, password) VALUES (?, ?)",
                          (values["username"], hash_password(values["password"])))
                conn.commit()
                sg.popup("Registration successful! Please log in.")
                window.close()
                break
            except sqlite3.IntegrityError:
                sg.popup("Username already exists. Please choose a different username.")
            finally:
                conn.close()
    window.close()

def client_window():
    window = sg.Window("Client Management", create_client_layout(), resizable=True, element_justification='l', size=(900, 600))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Add Client":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("""INSERT INTO clients (name, contact, email, address) VALUES (?, ?, ?, ?)""",
                      (values["name"], values["contact"], values["email"], values["address"]))
            conn.commit()
            conn.close()
            sg.popup("Client added successfully!")
        elif event == "View Clients":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("SELECT * FROM clients")
            rows = c.fetchall()
            conn.close()
            sg.popup_scrolled("Clients List", *[str(r) for r in rows])
    window.close()

def property_window():
    window = sg.Window("Property Management", create_property_layout(), resizable=True, element_justification='l', size=(900, 600))
    current_photo = None
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Lookup":
            try:
                conn = sqlite3.connect("primaris.db")
                c = conn.cursor()
                c.execute("SELECT id, name, location, price, status, photo FROM properties WHERE id=?",
                          (values["lookup_id"],))
                row = c.fetchone()
                conn.close()
                if row:
                    window["name"].update(row[1])
                    window["location"].update(row[2])
                    window["price"].update(row[3])
                    window["status"].update(row[4])
                    if row[5]:
                        window["photo_display"].update(data=row[5])
                        current_photo = row[5]
                    else:
                        window["photo_display"].update(data=sg.DEFAULT_BASE64_IMAGE)
                        current_photo = None
                else:
                    sg.popup("Property not found")
            except Exception as e:
                sg.popup(f"Error: {e}")
        elif event == "Upload Photo":
            path = sg.popup_get_file("Select Photo", file_types=(("PNG Files", "*.png"), ("GIF Files", "*.gif"), ("All Files", "*.*")))
            if path:
                try:
                    with open(path, "rb") as f:
                        current_photo = f.read()
                    window["photo_display"].update(data=current_photo)
                except Exception as e:
                    sg.popup(f"Error loading photo: {e}")
        elif event == "Add Property":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("""INSERT INTO properties (name, location, price, status, photo) VALUES (?, ?, ?, ?, ?)""",
                      (values["name"], values["location"], values["price"], values["status"], current_photo))
            conn.commit()
            conn.close()
            sg.popup("Property added successfully!")
            current_photo = None
        elif event == "View Properties":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("SELECT id, name, location, price, status FROM properties")
            rows = c.fetchall()
            conn.close()
            sg.popup_scrolled("Properties List", *[str(r) for r in rows])
    window.close()

def payment_plan_window():
    window = sg.Window("Payment Plan", create_payment_plan_layout(), resizable=True, element_justification='l', size=(900, 600))
    installment_amount = 0
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Calculate":
            try:
                total = float(values["total_amount"])
                down = float(values["down_payment"])
                num = int(values["installments"])
                remaining = total - down
                installment_amount = round(remaining / num, 2)
                window["calc_result"].update(f"Remaining: \u20b1{remaining:,.2f}  |  {num} installments of \u20b1{installment_amount:,.2f} each")
            except (ValueError, ZeroDivisionError):
                sg.popup("Enter valid numbers for total, down payment, and installments")
        if event == "Create Plan":
            try:
                total = float(values["total_amount"])
                down = float(values["down_payment"])
                num = int(values["installments"])
                remaining = total - down
                installment_amount = round(remaining / num, 2)
                conn = sqlite3.connect("primaris.db")
                c = conn.cursor()
                c.execute("""INSERT INTO payment_plans (client_id, property_id, total_amount, down_payment, installment_amount, total_installments, frequency, start_date)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                          (values["client_id"], values["property_id"], total, down, installment_amount, num,
                           values["frequency"], values["start_date"]))
                plan_id = c.lastrowid
                conn.commit()
                conn.close()
                create_installments(plan_id, values["client_id"], values["property_id"], num, installment_amount, values["start_date"], values["frequency"])
                sg.popup(f"Payment plan created! {num} installments of \u20b1{installment_amount:,.2f} each.")
                window.close()
                break
            except (ValueError, ZeroDivisionError):
                sg.popup("Fill all fields with valid values")
            except Exception as e:
                sg.popup(f"Error: {e}")
    window.close()

def installments_window():
    window = sg.Window("Installments", create_installments_layout(), resizable=True, element_justification='l', size=(900, 600))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Show All Pending":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("""SELECT id, client_id, installment_number, due_date, amount, status
                         FROM payment_installments WHERE status = 'Pending' ORDER BY due_date""")
            rows = c.fetchall()
            conn.close()
            if rows:
                sg.popup_scrolled("Pending Installments", *[str(r) for r in rows])
            else:
                sg.popup("No pending installments")
        if event == "Check Due Payments":
            due = check_due_payments()
            if due:
                sg.popup_scrolled("DUE PAYMENTS", *[f"Client {r[1]} |  #{r[2]}  | Due: {r[3]}  |  \u20b1{r[4]:,.2f}" for r in due])
            else:
                sg.popup("No due payments!")
        if event == "Mark as Paid":
            try:
                conn = sqlite3.connect("primaris.db")
                c = conn.cursor()
                today = datetime.now().strftime("%Y-%m-%d")
                c.execute("""UPDATE payment_installments SET status='Paid', paid_date=? WHERE id=?""",
                          (today, values["installment_id"]))
                if c.rowcount == 0:
                    sg.popup("No installment found with that ID")
                else:
                    conn.commit()
                    sg.popup("Installment marked as paid!")
                conn.close()
            except Exception as e:
                sg.popup(f"Error: {e}")
    window.close()

def payments_window():
    window = sg.Window("Payment Management", create_payments_layout(), resizable=True, element_justification='c', size=(900, 600))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Add Payment":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("INSERT INTO payments (client_id, property_id, amount, date, status) VALUES (?, ?, ?, ?, ?)",
                      (values["client_id"], values["property_id"], values["amount"], values["date"], values["status"]))
            conn.commit()
            conn.close()
            sg.popup("Payment added successfully!")
        elif event == "View Payments":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("SELECT * FROM payments")
            rows = c.fetchall()
            conn.close()
            sg.popup_scrolled("Payments List", *[str(r) for r in rows])
        elif event == "Setup Plan":
            payment_plan_window()
        elif event == "View Installments":
            installments_window()
        elif event == "Due Payments":
            due = check_due_payments()
            if due:
                sg.popup_scrolled("DUE PAYMENTS", *[f"Client {r[1]} |  #{r[2]}  | Due: {r[3]}  |  \u20b1{r[4]:,.2f}" for r in due])
            else:
                sg.popup("No due payments!")
    window.close()

def reports_window():
    window = sg.Window("Reports", create_reports_layout(), resizable=True, element_justification='c', size=(900, 600))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Generate Report":
            conn = sqlite3.connect("primaris.db")
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
                sg.popup_scrolled("Payments by Client", *[f"{r[0]}: \u20b1{r[1]}" for r in rows])
            elif report_type == "Payments by Property":
                c.execute("""SELECT properties.location, SUM(payments.amount)
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             GROUP BY properties.location""")
                rows = c.fetchall()
                sg.popup_scrolled("Payments by Property", *[f"{r[0]}: \u20b1{r[1]}" for r in rows])
            conn.close()
    window.close()

def login_window():
    window = sg.Window("Login", create_login_layout(), resizable=True, element_justification='c')
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        if event == "Register":
            register_window()
        if event == "Login":
            user = login(values["username"], values["password"])
            if user:
                conn = sqlite3.connect("primaris.db")
                c = conn.cursor()
                if user[3] == 1:
                    sg.popup("Welcome! This is your first login.")
                    c.execute("UPDATE employees SET first_login=0 WHERE id=?", (user[0],))
                    conn.commit()
                else:
                    sg.popup("Welcome back!")
                conn.close()
                window.close()
                dashboard()
            else:
                sg.popup("Invalid credentials")

    window.close()

# Dashboard Window
def dashboard():
    window = sg.Window("Primarius Realty Development", create_dashboard_layout(), resizable=True, element_justification='l')
    due = check_due_payments()
    if due:
        window["due_alert"].update(f"  {len(due)} due payment(s) \u2014 go to Payments to review")
    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, "Logout"):
            break
        elif event == "Manage Clients":
            client_window()
        elif event == "Manage Properties":
            property_window()
        elif event == "Manage Payments":
            payments_window()
        elif event == "Reports":
            reports_window()
    window.close()
    login_window()

# Run the application
if __name__ == "__main__":
    init_db()
    login_window()