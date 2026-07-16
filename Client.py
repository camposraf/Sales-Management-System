import sqlite3
import PySimpleGUI as sg
import hashlib
from datetime import datetime, timedelta
import calendar
from PIL import Image
import io

sg.theme("DarkBlue")

def next_id(table, prefix):
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()
    c.execute(f"SELECT id FROM {table} WHERE id LIKE '{prefix}-%'")
    rows = c.fetchall()
    conn.close()
    nums = [int(r[0].split("-")[1]) for r in rows if r[0] and "-" in r[0]]
    n = max(nums) + 1 if nums else 1
    return f"{prefix}-{n:03d}"

def resize_image_for_display(img_bytes, max_w=240, max_h=240):
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img.thumbnail((max_w, max_h), Image.LANCZOS)
    except Exception as e:
        sg.popup(f"Photo resize failed: {e}")
        return img_bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_client_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Add Client", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Clients", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
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
            [sg.Button("Add Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Properties", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Upload Photos", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Property ID:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="lookup_id", font=("Helvetica", 20), size=(10,1)),
             sg.Button("Lookup", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("Name:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="name", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Location:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="location", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Price:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="price", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Status:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="status", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("", size=(1,1))],
            [sg.Image(key="photo_display", size=(220, 220)),
             sg.Image(key="photo_display2", size=(220, 220))],
        ])],
    ]

def create_payments_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Add Payment", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Payments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Setup Plan", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Installments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Due Payments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
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
        [sg.Text("", size=(1,2))],
        [sg.Column([
            [sg.Button("Generate Report", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ], vertical_alignment='top'),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Select Report Type:", font=("Helvetica", 20), size=(20,1))],
            [sg.Combo(["Overdue Payments", "Payments by Client", "Payments by Property"], key="report_type", font=("Helvetica", 20), size=(25, 1))],
            [sg.Text("", size=(1,1))],
            [sg.Multiline(key="report_output", size=(65, 28), font=("Consolas", 11), disabled=True, autoscroll=True)],
        ], vertical_alignment='top')],
    ]

def create_dashboard_layout():
    client_tab = sg.Tab("Clients", [
        [sg.Column([
            [sg.Button("Add Client", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Clients", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Client Name:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="client_name", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Contact:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="client_contact", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Email:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="client_email", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Address:", font=("Helvetica", 20), size=(16,1)), sg.Input(key="client_address", font=("Helvetica", 20), size=(20,1))],
        ])],
    ])
    prop_tab = sg.Tab("Properties", [
        [sg.Column([
            [sg.Button("Add Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Properties", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Upload Photos", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Property ID:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="prop_lookup_id", font=("Helvetica", 20), size=(10,1)),
             sg.Button("Lookup", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("Name:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="prop_name", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Location:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="prop_location", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Price:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="prop_price", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("Status:", font=("Helvetica", 20), size=(14,1)), sg.Input(key="prop_status", font=("Helvetica", 20), size=(20,1))],
            [sg.Text("", size=(1,1))],
            [sg.Image(key="photo_display", size=(220, 220)),
             sg.Image(key="photo_display2", size=(220, 220))],
        ])],
    ])
    pay_tab = sg.Tab("Payments", [
        [sg.Column([
            [sg.Button("Add Payment", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Payments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Setup Plan", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("View Installments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Due Payments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Client ID", font=("Helvetica", 20), size=(18,1)), sg.Input(key="pay_client_id", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Property ID", font=("Helvetica", 20), size=(18,1)), sg.Input(key="pay_property_id", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Amount", font=("Helvetica", 20), size=(18,1)), sg.Input(key="pay_amount", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Date (YYYY-MM-DD)", font=("Helvetica", 20), size=(18,1)), sg.Input(key="pay_date", font=("Helvetica", 20), size=(12,1))],
            [sg.Text("Status", font=("Helvetica", 20), size=(18,1)), sg.Combo(["Paid", "Pending", "Overdue"], key="pay_status", font=("Helvetica", 20), size=(12,1))],
        ])],
    ])
    rpt_tab = sg.Tab("Reports", [
        [sg.Column([
            [sg.Button("Generate Report", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ], vertical_alignment='top'),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Select Report Type:", font=("Helvetica", 20), size=(20,1))],
            [sg.Combo(["Overdue Payments", "Payments by Client", "Payments by Property"], key="report_type", font=("Helvetica", 20), size=(25, 1))],
            [sg.Text("", size=(1,1))],
            [sg.Multiline(key="report_output", size=(65, 22), font=("Consolas", 11), disabled=True, autoscroll=True)],
        ], vertical_alignment='top')],
    ])
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", key="due_alert", font=("Helvetica", 16), text_color="red", justification="center")],
        [sg.TabGroup([[client_tab, prop_tab, pay_tab, rpt_tab]], tab_location='lefttab', font=("Helvetica", 14), expand_x=True)],
        [sg.Push(), sg.Button("Logout", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20)), sg.Push()],
    ]

def create_login_layout():
    return [
        [sg.Text("Primarius Realty Development", font=("Tahoma", 20), justification="center")],
        [sg.Text("", size=(5,5))],
        [sg.Text("Username:", font=("Tahoma", 20)), sg.Input(key="username", font=("Tahoma", 20), size=(20, 1))],
        [sg.Text("Password:", font=("Tahoma", 20)), sg.Input(key="password", password_char="*", font=("Tahoma", 20), size=(20, 1))],
        [sg.Text("", size=(1,1))],
        [sg.Button("Login", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Tahoma", 20))],
        [sg.Button("Register", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Tahoma", 20))],
        [sg.Button("Exit", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Tahoma", 20))]
    ]

def create_registration_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Register", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Username:", font=("Helvetica", 20), size=(12,1)), sg.Input(key="username", font=("Helvetica", 20), size=(20, 1))],
            [sg.Text("Password:", font=("Helvetica", 20), size=(12,1)), sg.Input(key="password", password_char="*", font=("Helvetica", 20), size=(20, 1))],
        ])],
    ]

def create_payment_plan_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Calculate", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Create Plan", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Client ID", font=("Helvetica", 20), size=(20,1)), sg.Input(key="client_id", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Property ID", font=("Helvetica", 20), size=(20,1)), sg.Input(key="property_id", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Total Amount", font=("Helvetica", 20), size=(20,1)), sg.Input(key="total_amount", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Down Payment", font=("Helvetica", 20), size=(20,1)), sg.Input(key="down_payment", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Frequency", font=("Helvetica", 20), size=(20,1)), sg.Combo(["6 Months", "12 Months"], key="frequency", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("Start Date (YY-MM-DD)", font=("Helvetica", 20), size=(20,1)), sg.Input(key="start_date", font=("Helvetica", 20), size=(15,1))],
            [sg.Text("", size=(1,1))],
            [sg.Text("", key="calc_result", font=("Helvetica", 16), text_color="yellow")],
        ])],
    ]

def create_installments_layout():
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", size=(2,2))],
        [sg.Column([
            [sg.Button("Show All Pending", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Check Due Payments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Mark as Paid", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
            [sg.Text("", size=(1,1))],
            [sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20))],
        ]),
        sg.VerticalSeparator(),
        sg.Column([
            [sg.Text("Installment ID to pay:", font=("Helvetica", 20), size=(22,1)), sg.Input(key="installment_id", font=("Helvetica", 20), size=(10,1))],
        ])],
    ]

def init_db():
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              first_login INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              role TEXT)""")
    for tbl, expected_type in [("clients", "TEXT"), ("properties", "TEXT"),
                                 ("payments", "TEXT"), ("payment_plans", "TEXT"),
                                 ("payment_installments", "TEXT")]:
        c.execute(f"PRAGMA table_info({tbl})")
        cols = c.fetchall()
        col_types = {r[1]: r[2].upper() for r in cols}
        if col_types.get("id") != expected_type:
            c.execute(f"DROP TABLE IF EXISTS {tbl}")
    c.execute("""CREATE TABLE IF NOT EXISTS clients(
        id TEXT PRIMARY KEY,
        name TEXT,
        contact TEXT,
        email TEXT,
        address TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS properties(
        id TEXT PRIMARY KEY,
        name TEXT,
        location TEXT,
        price REAL,
        status TEXT,
        photo BLOB,
        photo2 BLOB
    )""")
    try:
        c.execute("ALTER TABLE properties ADD COLUMN photo BLOB")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE properties ADD COLUMN photo2 BLOB")
    except sqlite3.OperationalError:
        pass
    c.execute("""CREATE TABLE IF NOT EXISTS payments(
        id TEXT PRIMARY KEY,
        client_id TEXT,
        property_id TEXT,
        amount REAL,
        date TEXT,
        status TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payment_plans(
        id TEXT PRIMARY KEY,
        client_id TEXT,
        property_id TEXT,
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
    c.execute("""CREATE TABLE IF NOT EXISTS payment_installments(
        id TEXT PRIMARY KEY,
        plan_id TEXT,
        client_id TEXT,
        property_id TEXT,
        installment_number INTEGER,
        due_date TEXT,
        amount REAL,
        paid_date TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(plan_id) REFERENCES payment_plans(id),
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    conn.commit()
    conn.close()

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
    c.execute("""SELECT pi.id, pi.client_id, pi.installment_number, pi.due_date, pi.amount, p.name
                 FROM payment_installments pi
                 JOIN properties p ON pi.property_id = p.id
                 WHERE pi.due_date <= ? AND pi.status = 'Pending'""", (today,))
    due = c.fetchall()
    conn.close()
    return due

def create_installments(plan_id, client_id, property_id, total_installments, installment_amount, start_date, frequency):
    conn = sqlite3.connect("primaris.db")
    c = conn.cursor()
    start = datetime.strptime(start_date, "%Y-%m-%d")
    ins_id = next_id("payment_installments", "INS")
    ins_num = int(ins_id.split("-")[1])
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
        c.execute("""INSERT INTO payment_installments (id, plan_id, client_id, property_id, installment_number, due_date, amount, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')""",
                  (f"INS-{ins_num + i:03d}", plan_id, client_id, property_id, i + 1, due.strftime("%Y-%m-%d"), installment_amount))
    conn.commit()
    conn.close()

def register_window():
    window = sg.Window("Register", create_registration_layout(), resizable=True, element_justification='c', size=(550, 350))
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
    window = sg.Window("Client Management", create_client_layout(), resizable=True, element_justification='c', size=(700, 400))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Add Client":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("""INSERT INTO clients (id, name, contact, email, address) VALUES (?, ?, ?, ?, ?)""",
                      (next_id("clients", "CLT"), values["name"], values["contact"], values["email"], values["address"]))
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
    window = sg.Window("Property Management", create_property_layout(), resizable=True, element_justification='c', size=(850, 550))
    current_photo = None
    current_photo2 = None
    current_property_id = None
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Lookup":
            try:
                conn = sqlite3.connect("primaris.db")
                c = conn.cursor()
                c.execute("SELECT id, name, location, price, status, photo, photo2 FROM properties WHERE id=?",
                          (values["lookup_id"],))
                row = c.fetchone()
                conn.close()
                if row:
                    current_property_id = row[0]
                    window["name"].update(row[1])
                    window["location"].update(row[2])
                    window["price"].update(row[3])
                    window["status"].update(row[4])
                    if row[5]:
                        resized = resize_image_for_display(row[5])
                        window["photo_display"].update(data=resized)
                        current_photo = row[5]
                    else:
                        window["photo_display"].update(data=sg.DEFAULT_BASE64_IMAGE)
                        current_photo = None
                    if row[6]:
                        resized2 = resize_image_for_display(row[6])
                        window["photo_display2"].update(data=resized2)
                        current_photo2 = row[6]
                    else:
                        window["photo_display2"].update(data=sg.DEFAULT_BASE64_IMAGE)
                        current_photo2 = None
                else:
                    sg.popup("Property not found")
            except Exception as e:
                sg.popup(f"Error: {e}")
        elif event == "Upload Photos":
            raw = sg.popup_get_file("Select up to 2 Photos", multiple_files=True, file_types=(("PNG Files", "*.png"), ("GIF Files", "*.gif"), ("All Files", "*.*")))
            if raw:
                files = raw.split(";") if isinstance(raw, str) else list(raw)
                files = [f.strip("'\" ") for f in files[:2]]
                try:
                    for i, p in enumerate(files):
                        with open(p, "rb") as f:
                            data = f.read()
                        if i == 0:
                            current_photo = data
                            resized = resize_image_for_display(data)
                            window["photo_display"].update(data=resized)
                        else:
                            current_photo2 = data
                            resized2 = resize_image_for_display(data)
                            window["photo_display2"].update(data=resized2)
                except Exception as e:
                    sg.popup(f"Error loading photo: {e}")
        elif event == "Add Property":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            new_id = next_id("properties", "PRP")
            c.execute("""INSERT INTO properties (id, name, location, price, status, photo, photo2) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (new_id, values["name"], values["location"], values["price"], values["status"], current_photo, current_photo2))
            conn.commit()
            current_property_id = new_id
            conn.close()
            sg.popup("Property added successfully!")
            current_photo = None
            current_photo2 = None
        elif event == "View Properties":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("SELECT id, name, location, price, status FROM properties")
            rows = c.fetchall()
            conn.close()
            sg.popup_scrolled("Properties List", *[str(r) for r in rows])
    window.close()

def payment_plan_window():
    window = sg.Window("Payment Plan", create_payment_plan_layout(), resizable=True, element_justification='c', size=(750, 520))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Calculate":
            try:
                total = float(values["total_amount"])
                down = float(values["down_payment"])
                freq = values["frequency"]
                num = 6 if freq == "6 Months" else 12
                remaining = total - down
                installment_amount = round(remaining / num, 2)
                window["calc_result"].update(f"Remaining: \u20b1{remaining:,.2f}  |  {num} monthly installments of \u20b1{installment_amount:,.2f} each")
            except (ValueError, ZeroDivisionError):
                sg.popup("Enter valid numbers for total and down payment, and select a frequency")
        if event == "Create Plan":
            try:
                total = float(values["total_amount"])
                down = float(values["down_payment"])
                freq = values["frequency"]
                num = 6 if freq == "6 Months" else 12
                remaining = total - down
                installment_amount = round(remaining / num, 2)
                conn = sqlite3.connect("primaris.db")
                c = conn.cursor()
                plan_id = next_id("payment_plans", "PLN")
                c.execute("""INSERT INTO payment_plans (id, client_id, property_id, total_amount, down_payment, installment_amount, total_installments, frequency, start_date)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (plan_id, values["client_id"], values["property_id"], total, down, installment_amount, num,
                           values["frequency"], values["start_date"]))
                conn.commit()
                conn.close()
                create_installments(plan_id, values["client_id"], values["property_id"], num, installment_amount, values["start_date"], "Monthly")
                sg.popup(f"Payment plan created! {num} monthly installments of \u20b1{installment_amount:,.2f} each.")
                window.close()
                break
            except (ValueError, ZeroDivisionError):
                sg.popup("Fill all fields with valid values")
            except Exception as e:
                sg.popup(f"Error: {e}")
    window.close()

def installments_window():
    window = sg.Window("Installments", create_installments_layout(), resizable=True, element_justification='c', size=(650, 420))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Show All Pending":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("""SELECT pi.id, pi.client_id, p.name, pi.installment_number, pi.due_date, pi.amount, pi.status
                         FROM payment_installments pi
                         JOIN properties p ON pi.property_id = p.id
                         WHERE pi.status = 'Pending' ORDER BY pi.due_date""")
            rows = c.fetchall()
            conn.close()
            if rows:
                sg.popup_scrolled("Pending Installments", *[f"{r[0]} | Client {r[1]} | {r[2]} | #{r[3]} | Due: {r[4]} | \u20b1{r[5]:,.2f} | {r[6]}" for r in rows])
            else:
                sg.popup("No pending installments")
        if event == "Check Due Payments":
            due = check_due_payments()
            if due:
                sg.popup_scrolled("DUE PAYMENTS", *[f"{r[0]} | Client {r[1]} | {r[5]} |  #{r[2]}  | Due: {r[3]}  |  \u20b1{r[4]:,.2f}" for r in due])
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
    window = sg.Window("Payment Management", create_payments_layout(), resizable=True, element_justification='c', size=(750, 520))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Add Payment":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("INSERT INTO payments (id, client_id, property_id, amount, date, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (next_id("payments", "PAY"), values["client_id"], values["property_id"], values["amount"], values["date"], values["status"]))
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
                sg.popup_scrolled("DUE PAYMENTS", *[f"{r[0]} | Client {r[1]} | {r[5]} |  #{r[2]}  | Due: {r[3]}  |  \u20b1{r[4]:,.2f}" for r in due])
            else:
                sg.popup("No due payments!")
    window.close()

def reports_window():
    window = sg.Window("Reports", create_reports_layout(), resizable=True, element_justification='c', size=(800, 600))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "Generate Report":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            report_type = values["report_type"]
            output = ""
            def fmt_date(d):
                if not d:
                    return "--:--:----"
                parts = d.split("-")
                if len(parts) == 3:
                    return f"{parts[1]}:{parts[2]}:{parts[0]}"
                return d

            if report_type == "Overdue Payments":
                c.execute("""SELECT payments.date, properties.name, payments.amount
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             WHERE payments.status='Overdue'""")
                rows = c.fetchall()
                if rows:
                    output = f"{'OVERDUE PAYMENTS':^55}\n"
                    output += "="*55 + "\n\n"
                    for r in rows:
                        output += f"  [{fmt_date(r[0]):>12}]  {r[1]:<25}  \u20b1{r[2]:>8,.2f}\n"
                else:
                    output = "No overdue payments found."
            elif report_type == "Payments by Client":
                c.execute("""SELECT clients.name, SUM(payments.amount), MAX(payments.date), COUNT(payments.id)
                             FROM payments
                             JOIN clients ON payments.client_id = clients.id
                             GROUP BY clients.name
                             ORDER BY SUM(payments.amount) DESC""")
                rows = c.fetchall()
                if rows:
                    output = f"{'PAYMENTS BY CLIENT':^55}\n"
                    output += "="*55 + "\n\n"
                    for r in rows:
                        output += f"  {r[0]:<20}  \u20b1{r[1]:>8,.2f}  [{fmt_date(r[2]):>12}]  {r[3]}\n"
                else:
                    output = "No payment data found."
            elif report_type == "Payments by Property":
                c.execute("""SELECT properties.location, SUM(payments.amount), MAX(payments.date), COUNT(payments.id)
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             GROUP BY properties.location
                             ORDER BY SUM(payments.amount) DESC""")
                rows = c.fetchall()
                if rows:
                    output = f"{'PAYMENTS BY PROPERTY':^55}\n"
                    output += "="*55 + "\n\n"
                    for r in rows:
                        output += f"  {r[0]:<20}  \u20b1{r[1]:>8,.2f}  [{fmt_date(r[2]):>12}]  {r[3]}\n"
                else:
                    output = "No payment data found."
            conn.close()
            window["report_output"].update(output)
    window.close()

def login_window():
    window = sg.Window("Login", create_login_layout(), resizable=True, element_justification='c', size=(550, 450))
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
                break
            else:
                sg.popup("Invalid credentials")
    window.close()

def dashboard():
    window = sg.Window("Sales Management System", create_dashboard_layout(), resizable=True, element_justification='c', size=(950, 700))
    current_photo = None
    current_photo2 = None
    current_property_id = None
    due = check_due_payments()
    if due:
        window["due_alert"].update(f"  {len(due)} due payment(s) \u2014 go to Payments tab")
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Logout"):
            break
        if event == "Add Client":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("""INSERT INTO clients (id, name, contact, email, address) VALUES (?, ?, ?, ?, ?)""",
                      (next_id("clients", "CLT"), values["client_name"], values["client_contact"], values["client_email"], values["client_address"]))
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
        elif event == "Lookup":
            try:
                conn = sqlite3.connect("primaris.db")
                c = conn.cursor()
                c.execute("SELECT id, name, location, price, status, photo, photo2 FROM properties WHERE id=?",
                          (values["prop_lookup_id"],))
                row = c.fetchone()
                conn.close()
                if row:
                    current_property_id = row[0]
                    window["prop_name"].update(row[1])
                    window["prop_location"].update(row[2])
                    window["prop_price"].update(row[3])
                    window["prop_status"].update(row[4])
                    if row[5]:
                        resized = resize_image_for_display(row[5])
                        window["photo_display"].update(data=resized)
                        current_photo = row[5]
                    else:
                        window["photo_display"].update(data=sg.DEFAULT_BASE64_IMAGE)
                        current_photo = None
                    if row[6]:
                        resized2 = resize_image_for_display(row[6])
                        window["photo_display2"].update(data=resized2)
                        current_photo2 = row[6]
                    else:
                        window["photo_display2"].update(data=sg.DEFAULT_BASE64_IMAGE)
                        current_photo2 = None
                else:
                    sg.popup("Property not found")
            except Exception as e:
                sg.popup(f"Error: {e}")
        elif event == "Upload Photos":
            raw = sg.popup_get_file("Select up to 2 Photos", multiple_files=True, file_types=(("PNG Files", "*.png"), ("GIF Files", "*.gif"), ("All Files", "*.*")))
            if raw:
                files = raw.split(";") if isinstance(raw, str) else list(raw)
                files = [f.strip("'\" ") for f in files[:2]]
                try:
                    for i, p in enumerate(files):
                        with open(p, "rb") as f:
                            data = f.read()
                        if i == 0:
                            current_photo = data
                            resized = resize_image_for_display(data)
                            window["photo_display"].update(data=resized)
                        else:
                            current_photo2 = data
                            resized2 = resize_image_for_display(data)
                            window["photo_display2"].update(data=resized2)
                except Exception as e:
                    sg.popup(f"Error loading photo: {e}")
        elif event == "Add Property":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            new_id = next_id("properties", "PRP")
            c.execute("""INSERT INTO properties (id, name, location, price, status, photo, photo2) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (new_id, values["prop_name"], values["prop_location"], values["prop_price"], values["prop_status"], current_photo, current_photo2))
            conn.commit()
            current_property_id = new_id
            conn.close()
            sg.popup("Property added successfully!")
            current_photo = None
            current_photo2 = None
        elif event == "View Properties":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("SELECT id, name, location, price, status FROM properties")
            rows = c.fetchall()
            conn.close()
            sg.popup_scrolled("Properties List", *[str(r) for r in rows])
        elif event == "Add Payment":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            c.execute("INSERT INTO payments (id, client_id, property_id, amount, date, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (next_id("payments", "PAY"), values["pay_client_id"], values["pay_property_id"], values["pay_amount"], values["pay_date"], values["pay_status"]))
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
                sg.popup_scrolled("DUE PAYMENTS", *[f"{r[0]} | Client {r[1]} | {r[5]} |  #{r[2]}  | Due: {r[3]}  |  \u20b1{r[4]:,.2f}" for r in due])
            else:
                sg.popup("No due payments!")
        elif event == "Generate Report":
            conn = sqlite3.connect("primaris.db")
            c = conn.cursor()
            report_type = values["report_type"]
            output = ""
            def fmt_date(d):
                if not d:
                    return "--:--:----"
                parts = d.split("-")
                if len(parts) == 3:
                    return f"{parts[1]}:{parts[2]}:{parts[0]}"
                return d
            if report_type == "Overdue Payments":
                c.execute("""SELECT payments.date, properties.name, payments.amount
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             WHERE payments.status='Overdue'""")
                rows = c.fetchall()
                if rows:
                    output = f"{'OVERDUE PAYMENTS':^55}\n"
                    output += "="*55 + "\n\n"
                    for r in rows:
                        output += f"  [{fmt_date(r[0]):>12}]  {r[1]:<25}  \u20b1{r[2]:>8,.2f}\n"
                else:
                    output = "No overdue payments found."
            elif report_type == "Payments by Client":
                c.execute("""SELECT clients.name, SUM(payments.amount), MAX(payments.date), COUNT(payments.id)
                             FROM payments
                             JOIN clients ON payments.client_id = clients.id
                             GROUP BY clients.name
                             ORDER BY SUM(payments.amount) DESC""")
                rows = c.fetchall()
                if rows:
                    output = f"{'PAYMENTS BY CLIENT':^55}\n"
                    output += "="*55 + "\n\n"
                    for r in rows:
                        output += f"  {r[0]:<20}  \u20b1{r[1]:>8,.2f}  [{fmt_date(r[2]):>12}]  {r[3]}\n"
                else:
                    output = "No payment data found."
            elif report_type == "Payments by Property":
                c.execute("""SELECT properties.location, SUM(payments.amount), MAX(payments.date), COUNT(payments.id)
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             GROUP BY properties.location
                             ORDER BY SUM(payments.amount) DESC""")
                rows = c.fetchall()
                if rows:
                    output = f"{'PAYMENTS BY PROPERTY':^55}\n"
                    output += "="*55 + "\n\n"
                    for r in rows:
                        output += f"  {r[0]:<20}  \u20b1{r[1]:>8,.2f}  [{fmt_date(r[2]):>12}]  {r[3]}\n"
                else:
                    output = "No payment data found."
            conn.close()
            window["report_output"].update(output)
    window.close()
    login_window()

if __name__ == "__main__":
    init_db()
    login_window()
