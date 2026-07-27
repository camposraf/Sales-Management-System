import sqlite3
import PySimpleGUI as sg
import hashlib
from datetime import datetime
import calendar
from PIL import Image
import io

sg.theme("DarkBlue")

def next_id(table, prefix):
    conn = sqlite3.connect("primarius.db")
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

def search_properties(keyword):
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    q = f"%{keyword}%"
    c.execute("""SELECT id, name, location, price, status, client_name 
                 FROM properties 
                 WHERE name LIKE ? OR location LIKE ? OR status LIKE ? 
                 OR client_name LIKE ? OR id LIKE ?""",
              (q, q, q, q, q))
    rows = c.fetchall()
    conn.close()
    return rows

def get_property_by_id(prop_id):
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    c.execute("SELECT id, name, location, price, status, client_name, client_contact, client_email, client_address, photo, photo2 FROM properties WHERE id=?", (prop_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "name": row[1], "location": row[2], "price": row[3],
            "status": row[4], "client_name": row[5], "client_contact": row[6],
            "client_email": row[7], "client_address": row[8], "photo": row[9], "photo2": row[10]
        }
    return None

def format_contact(value):
    digits = "".join(c for c in value if c.isdigit())
    if digits.startswith("63") and len(digits) >= 12:
        return f"+63 {digits[2:5]}-{digits[5:8]}-{digits[8:12]}"
    elif digits.startswith("0") and len(digits) >= 11:
        return f"+63 {digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
    elif len(digits) >= 10:
        return f"+63 {digits[:3]}-{digits[3:6]}-{digits[6:10]}"
    elif len(digits) > 0:
        return f"+63 {digits}"
    return "+63 "

def strip_contact_prefix(value):
    return value.replace("+63 ", "").replace("+63", "")

def sanitize_contact_input(value):
    if not value or not value.startswith("+63"):
        value = "+63 " + value
    stripped = value.replace("+63 ", "").replace("+63", "")
    digits = "".join(c for c in stripped if c.isdigit())
    if digits.startswith("0"):
        digits = digits[1:]
    digits = digits[:10]
    if digits:
        return f"+63 {digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return "+63 "

def property_details_popup(prop):
    photo_col = []
    if prop["photo"]:
        resized = resize_image_for_display(prop["photo"])
        photo_col.append([sg.Image(data=resized, key="-PHOTO1-")])
    if prop["photo2"]:
        resized2 = resize_image_for_display(prop["photo2"])
        photo_col.append([sg.Image(data=resized2, key="-PHOTO2-")])

    try:
        price_str = f"\u20b1{float(prop['price']):,.2f}" if prop['price'] else "--"
    except (ValueError, TypeError):
        price_str = "--"

    layout = [
        [sg.Text("Property Details", font=("Helvetica", 20), justification="center")],
        [sg.Text(f"ID: {prop['id']}", font=("Helvetica", 16))],
        [sg.Text(f"Name: {prop['name'] or ''}", font=("Helvetica", 16))],
        [sg.Text(f"Location: {prop['location'] or ''}", font=("Helvetica", 16))],
        [sg.Text(f"Price: {price_str}", font=("Helvetica", 16))],
        [sg.Text(f"Status: {prop['status'] or ''}", font=("Helvetica", 16))],
        [sg.HorizontalSeparator()],
        [sg.Text("Client Information", font=("Helvetica", 16))],
        [sg.Text(f"Name: {prop['client_name'] or ''}", font=("Helvetica", 14))],
        [sg.Text(f"Contact: {prop['client_contact'] or ''}", font=("Helvetica", 14))],
        [sg.Text(f"Email: {prop['client_email'] or ''}", font=("Helvetica", 14))],
        [sg.Text(f"Address: {prop['client_address'] or ''}", font=("Helvetica", 14))],
    ]
    if photo_col:
        layout.append([sg.HorizontalSeparator()])
        layout.append([sg.Text("Photos", font=("Helvetica", 16))])
        layout.append([sg.Column(photo_col, justification="center")])
    layout.append([sg.Push(), sg.Button("Close", font=("Helvetica", 14)), sg.Push()])

    sg.Window("Property Details", layout, size=(800, 600), resizable=False, element_justification='c', modal=True, finalize=True).read(close=True)

def create_dashboard_layout():
    prop_tab = sg.Tab("Properties", [
        [sg.Push(), sg.Button("Manage Properties", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 16)),
         sg.Button("Add Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 16)), sg.Push()],
        [sg.Text("Search:", font=("Helvetica", 16)), sg.Input(key="search_keyword", font=("Helvetica", 16), size=(30,1), expand_x=True),
         sg.Button("Search", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14))],
        [sg.Table(
            values=[["", "", "", "", "", ""]],
            headings=["ID", "Name", "Location", "Price", "Status", "Client"],
            key="prop_search_results",
            font=("Helvetica", 12),
            justification="left",
            num_rows=6,
            auto_size_columns=True,
            visible=False,
            enable_click_events=True,
            expand_x=True
        )],
        [sg.HorizontalSeparator()],
        [sg.Text("SELECTED PROPERTY", font=("Helvetica", 14, "bold"), visible=False, key="-DETAIL_HEADER-")],
        [sg.Column([
            [sg.Text("Name:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_NAME-", font=("Helvetica", 12), size=(30,1)),
             sg.Text("Location:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_LOCATION-", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Price:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_PRICE-", font=("Helvetica", 12), size=(30,1)),
             sg.Text("Status:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_STATUS-", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Client:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_CLIENT-", font=("Helvetica", 12), size=(30,1)),
             sg.Text("Contact:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_CONTACT-", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Email:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_EMAIL-", font=("Helvetica", 12), size=(30,1)),
             sg.Text("Address:", font=("Helvetica", 12), size=(10,1)), sg.Text("", key="-DETAIL_ADDRESS-", font=("Helvetica", 12), size=(25,1))],
        ], visible=False, key="-DETAIL_FIELDS-")],
        [sg.Column([
            [sg.Image(key="-DETAIL_PHOTO1-", size=(200, 200)), sg.Image(key="-DETAIL_PHOTO2-", size=(200, 200))]
        ], visible=False, key="-DETAIL_PHOTOS-")],
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
        [sg.TabGroup([[prop_tab, pay_tab, rpt_tab]], tab_location='lefttab', font=("Helvetica", 14), expand_x=True, size=(1100, 650))],
        [sg.Push(), sg.Button("Logout", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20)), sg.Push()],
    ]

def create_property_management_layout():
    return [
        [sg.Text("Manage Properties", font=("Helvetica", 20), justification="center", pad=(0, (10, 15)))],
        [sg.Text("Search:", font=("Helvetica", 16), pad=(0, 5)), sg.Input(key="prop_search_keyword", font=("Helvetica", 16), size=(30,1), expand_x=True, pad=(5, 5)),
         sg.Button("Search", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14), pad=(5, 5))],
        [sg.Table(
            values=[["", "", "", "", "", ""]],
            headings=["ID", "Name", "Location", "Price", "Status", "Client"],
            key="prop_search_results",
            font=("Helvetica", 12),
            justification="left",
            num_rows=5,
            auto_size_columns=True,
            visible=False,
            enable_click_events=True,
            expand_x=True,
            pad=(0, 10)
        )],
        [sg.HorizontalSeparator()],
        [sg.Column([
            [sg.Text("Property Details", font=("Helvetica", 14, "bold"), pad=(0, (5, 10)))],
            [sg.Text("Name:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Input(key="prop_name", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
            [sg.Text("Location:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Input(key="prop_location", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
            [sg.Text("Price:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Input(key="prop_price", default_text="\u20b1", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
            [sg.Text("Status:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Combo(["Sold", "Unsold"], key="prop_status", font=("Helvetica", 12), size=(22,1), readonly=True, pad=(5, 6))],
        ], pad=(0, 0)),
        sg.Column([
            [sg.Text("Client Information", font=("Helvetica", 14, "bold"), pad=(0, (5, 10)))],
            [sg.Text("Name:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Input(key="prop_client_name", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
            [sg.Text("Contact:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Input(key="prop_client_contact", default_text="+63 ", font=("Helvetica", 12), size=(25,1), pad=(5, 6), enable_events=True)],
            [sg.Text("Email:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Input(key="prop_client_email", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
            [sg.Text("Address:", font=("Helvetica", 12), size=(10,1), pad=(0, 6)), sg.Input(key="prop_client_address", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
        ], pad=(0, 0))],
        [sg.Push(), sg.Button("Upload Photos", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 12), pad=(3, 8)),
                    sg.Button("Update Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 12), pad=(3, 8)),
                    sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 12), pad=(3, 8))],
        [sg.Image(key="photo_display", size=(200, 200), pad=(10, 5)),
         sg.Image(key="photo_display2", size=(200, 200), pad=(10, 5))],
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
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              first_login INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              role TEXT)""")
    try:
        c.execute("ALTER TABLE employees ADD COLUMN first_login INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    c.execute("DROP TABLE IF EXISTS clients")
    for tbl in ["properties", "payments", "payment_plans", "payment_installments"]:
        c.execute(f"PRAGMA table_info({tbl})")
        cols = c.fetchall()
        col_types = {r[1]: r[2].upper() for r in cols}
        if col_types.get("id") != "TEXT":
            c.execute(f"DROP TABLE IF EXISTS {tbl}")
    c.execute("""CREATE TABLE IF NOT EXISTS properties(
        id TEXT PRIMARY KEY,
        name TEXT,
        location TEXT,
        price REAL,
        status TEXT,
        client_name TEXT,
        client_contact TEXT,
        client_email TEXT,
        client_address TEXT,
        photo BLOB,
        photo2 BLOB
    )""")
    for col in ["client_name", "client_contact", "client_email", "client_address", "photo", "photo2"]:
        try:
            c.execute(f"ALTER TABLE properties ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    c.execute("""CREATE TABLE IF NOT EXISTS payments(
        id TEXT PRIMARY KEY,
        property_id TEXT,
        amount REAL,
        date TEXT,
        status TEXT,
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payment_plans(
        id TEXT PRIMARY KEY,
        property_id TEXT,
        total_amount REAL,
        down_payment REAL,
        installment_amount REAL,
        total_installments INTEGER,
        frequency TEXT,
        start_date TEXT,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payment_installments(
        id TEXT PRIMARY KEY,
        plan_id TEXT,
        property_id TEXT,
        installment_number INTEGER,
        due_date TEXT,
        amount REAL,
        paid_date TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(plan_id) REFERENCES payment_plans(id),
        FOREIGN KEY(property_id) REFERENCES properties(id)
    )""")
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE username=? AND password=?",
              (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result

def check_due_payments():
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""SELECT pi.id, p.client_name, pi.installment_number, pi.due_date, pi.amount, p.name
                 FROM payment_installments pi
                 JOIN properties p ON pi.property_id = p.id
                 WHERE pi.due_date <= ? AND pi.status = 'Pending'""", (today,))
    due = c.fetchall()
    conn.close()
    return due

def create_installments(plan_id, property_id, total_installments, installment_amount, start_date, frequency):
    conn = sqlite3.connect("primarius.db")
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
        else:
            due = datetime(start.year + i + 1, start.month, min(start.day, calendar.monthrange(start.year + i + 1, start.month)[1]))
        c.execute("""INSERT INTO payment_installments (id, plan_id, property_id, installment_number, due_date, amount, status)
                     VALUES (?, ?, ?, ?, ?, ?, 'Pending')""",
                  (f"INS-{ins_num + i:03d}", plan_id, property_id, i + 1, due.strftime("%Y-%m-%d"), installment_amount))
    conn.commit()
    conn.close()

def register_window():
    window = sg.Window("Register", create_registration_layout(), resizable=True, element_justification='c', size=(550, 350))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED,):
            break
        if event == "Register":
            conn = sqlite3.connect("primarius.db")
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
                conn = sqlite3.connect("primarius.db")
                c = conn.cursor()
                plan_id = next_id("payment_plans", "PLN")
                c.execute("""INSERT INTO payment_plans (id, property_id, total_amount, down_payment, installment_amount, total_installments, frequency, start_date)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                          (plan_id, values["property_id"], total, down, installment_amount, num,
                           values["frequency"], values["start_date"]))
                conn.commit()
                conn.close()
                create_installments(plan_id, values["property_id"], num, installment_amount, values["start_date"], "Monthly")
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
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            c.execute("""SELECT pi.id, p.client_name, p.name, pi.installment_number, pi.due_date, pi.amount, pi.status
                         FROM payment_installments pi
                         JOIN properties p ON pi.property_id = p.id
                         WHERE pi.status = 'Pending' ORDER BY pi.due_date""")
            rows = c.fetchall()
            conn.close()
            if rows:
                sg.popup_scrolled("Pending Installments", *[f"{r[0]} | {r[1]} | {r[2]} | #{r[3]} | Due: {r[4]} | \u20b1{r[5]:,.2f} | {r[6]}" for r in rows])
            else:
                sg.popup("No pending installments")
        if event == "Check Due Payments":
            due = check_due_payments()
            if due:
                sg.popup_scrolled("DUE PAYMENTS", *[f"{r[0]} | {r[1]} | {r[5]} |  #{r[2]}  | Due: {r[3]}  |  \u20b1{r[4]:,.2f}" for r in due])
            else:
                sg.popup("No due payments!")
        if event == "Mark as Paid":
            try:
                conn = sqlite3.connect("primarius.db")
                c = conn.cursor()
                today = datetime.now().strftime("%Y-%m-%d")
                c.execute("SELECT property_id, amount FROM payment_installments WHERE id=?",
                          (values["installment_id"],))
                row = c.fetchone()
                if not row:
                    sg.popup("No installment found with that ID")
                else:
                    prop_id, amount = row
                    c.execute("""UPDATE payment_installments SET status='Paid', paid_date=? WHERE id=?""",
                              (today, values["installment_id"]))
                    pay_id = next_id("payments", "PAY")
                    c.execute("INSERT INTO payments (id, property_id, amount, date, status) VALUES (?, ?, ?, ?, ?)",
                              (pay_id, prop_id, amount, today, "Paid"))
                    conn.commit()
                    sg.popup("Installment marked as paid! Payment recorded in ledger.")
                conn.close()
            except Exception as e:
                sg.popup(f"Error: {e}")
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
                conn = sqlite3.connect("primarius.db")
                c = conn.cursor()
                if user[4] == 1:
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

def manage_properties_window(prop_id=None):
    window = sg.Window("Manage Properties", create_property_management_layout(), resizable=False, element_justification='c', size=(950, 750), finalize=True)
    prop_search_cache = []
    current_prop_id = None
    current_photo = None
    current_photo2 = None
    if prop_id:
        current_prop_id = prop_id
        conn = sqlite3.connect("primarius.db")
        c = conn.cursor()
        c.execute("SELECT id, name, location, price, status, client_name, client_contact, client_email, client_address, photo, photo2 FROM properties WHERE id=?", (prop_id,))
        row = c.fetchone()
        conn.close()
        if row:
            window["prop_name"].update(row[1] or "")
            window["prop_location"].update(row[2] or "")
            price_val = f"\u20b1{float(row[3]):,.2f}" if row[3] else "\u20b1"
            window["prop_price"].update(price_val)
            window["prop_status"].update(row[4] or "")
            window["prop_client_name"].update(row[5] or "")
            window["prop_client_contact"].update(format_contact(row[6] or ""))
            window["prop_client_email"].update(row[7] or "")
            window["prop_client_address"].update(row[8] or "")
            if row[9]:
                resized = resize_image_for_display(row[9])
                window["photo_display"].update(data=resized)
            if row[10]:
                resized2 = resize_image_for_display(row[10])
                window["photo_display2"].update(data=resized2)
            prop_search_cache = search_properties(row[1] or row[0])
            if prop_search_cache:
                table_data = [[r[0], r[1] or "", r[2] or "", f"\u20b1{r[3]:,.2f}", r[4] or "", r[5] or ""] for r in prop_search_cache]
                window["prop_search_results"].update(values=table_data, visible=True)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "prop_client_contact":
            window["prop_client_contact"].update(sanitize_contact_input(values["prop_client_contact"]))
        if event == "Search":
            keyword = values["prop_search_keyword"].strip()
            if not keyword:
                sg.popup("Enter a keyword to search")
                continue
            prop_search_cache = search_properties(keyword)
            if prop_search_cache:
                table_data = [[r[0], r[1] or "", r[2] or "", f"\u20b1{r[3]:,.2f}", r[4] or "", r[5] or ""] for r in prop_search_cache]
                window["prop_search_results"].update(values=table_data, visible=True)
            else:
                window["prop_search_results"].update(values=[["", "", "", "", "", ""]], visible=False)
                sg.popup(f"No properties found matching '{keyword}'")
        elif isinstance(event, tuple) and event[0] == "prop_search_results":
            if len(event) > 2 and event[2] is not None and isinstance(event[2], tuple) and event[2][0] is not None:
                row_idx = event[2][0]
                if row_idx < len(prop_search_cache):
                    current_prop_id = prop_search_cache[row_idx][0]
                    conn = sqlite3.connect("primarius.db")
                    c = conn.cursor()
                    c.execute("SELECT id, name, location, price, status, client_name, client_contact, client_email, client_address, photo, photo2 FROM properties WHERE id=?", (current_prop_id,))
                    row = c.fetchone()
                    conn.close()
                    if row:
                        window["prop_name"].update(row[1])
                        window["prop_location"].update(row[2])
                        price_val = f"\u20b1{float(row[3]):,.2f}" if row[3] else "\u20b1"
                        window["prop_price"].update(price_val)
                        window["prop_status"].update(row[4])
                        window["prop_client_name"].update(row[5])
                        window["prop_client_contact"].update(format_contact(row[6] or ""))
                        window["prop_client_email"].update(row[7])
                        window["prop_client_address"].update(row[8])
                        if row[9]:
                            resized = resize_image_for_display(row[9])
                            window["photo_display"].update(data=resized)
                            current_photo = row[9]
                        else:
                            window["photo_display"].update(data=sg.DEFAULT_BASE64_IMAGE)
                            current_photo = None
                        if row[10]:
                            resized2 = resize_image_for_display(row[10])
                            window["photo_display2"].update(data=resized2)
                            current_photo2 = row[10]
                        else:
                            window["photo_display2"].update(data=sg.DEFAULT_BASE64_IMAGE)
                            current_photo2 = None
                    else:
                        window["photo_display2"].update(data=sg.DEFAULT_BASE64_IMAGE)
        elif event == "Update Property":
            if not current_prop_id:
                sg.popup("No property selected! Search and click a property first.")
                continue
            contact_val = format_contact(values["prop_client_contact"])
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            price_val = values["prop_price"].replace("\u20b1", "").replace(",", "").strip()
            c.execute("""UPDATE properties SET name=?, location=?, price=?, status=?,
                         client_name=?, client_contact=?, client_email=?, client_address=?,
                         photo=?, photo2=? WHERE id=?""",
                      (values["prop_name"], values["prop_location"], price_val, values["prop_status"],
                       values["prop_client_name"], contact_val, values["prop_client_email"], values["prop_client_address"],
                       current_photo, current_photo2, current_prop_id))
            conn.commit()
            conn.close()
            sg.popup("Property updated successfully!")
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
    window.close()

def create_add_property_layout():
    return [
        [sg.Text("Add Property", font=("Helvetica", 20), justification="center")],
        [sg.Column([
            [sg.Text("Property Details", font=("Helvetica", 14, "bold"))],
            [sg.Text("Name:", font=("Helvetica", 12), size=(10,1)), sg.Input(key="prop_name", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Location:", font=("Helvetica", 12), size=(10,1)), sg.Input(key="prop_location", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Price:", font=("Helvetica", 12), size=(10,1)), sg.Input(key="prop_price", default_text="\u20b1", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Status:", font=("Helvetica", 12), size=(10,1)), sg.Combo(["Sold", "Unsold"], key="prop_status", font=("Helvetica", 12), size=(22,1), readonly=True)],
        ]),
        sg.Column([
            [sg.Text("Client Information", font=("Helvetica", 14, "bold"))],
            [sg.Text("Name:", font=("Helvetica", 12), size=(10,1)), sg.Input(key="prop_client_name", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Contact:", font=("Helvetica", 12), size=(10,1)), sg.Input(key="prop_client_contact", default_text="+63 ", font=("Helvetica", 12), size=(25,1), enable_events=True)],
            [sg.Text("Email:", font=("Helvetica", 12), size=(10,1)), sg.Input(key="prop_client_email", font=("Helvetica", 12), size=(25,1))],
            [sg.Text("Address:", font=("Helvetica", 12), size=(10,1)), sg.Input(key="prop_client_address", font=("Helvetica", 12), size=(25,1))],
        ])],
        [sg.Push(), sg.Button("Add Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
                 sg.Button("Upload Photos", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
                 sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14))],
        [sg.Image(key="photo_display", size=(200, 200)),
         sg.Image(key="photo_display2", size=(200, 200))],
        
    ]

def add_property_window():
    window = sg.Window("Add Property", create_add_property_layout(), resizable=False, element_justification='c', size=(900, 650), finalize=True)
    current_photo = None
    current_photo2 = None
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        elif event == "prop_client_contact":
            window["prop_client_contact"].update(sanitize_contact_input(values["prop_client_contact"]))
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
            if not values["prop_name"].strip():
                sg.popup("Property name is required!")
                continue
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            new_id = next_id("properties", "PRP")
            price_val = values["prop_price"].replace("\u20b1", "").replace(",", "").strip()
            contact_val = format_contact(values["prop_client_contact"])
            c.execute("""INSERT INTO properties (id, name, location, price, status, client_name, client_contact, client_email, client_address, photo, photo2) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (new_id, values["prop_name"], values["prop_location"], price_val, values["prop_status"],
                       values["prop_client_name"], contact_val, values["prop_client_email"], values["prop_client_address"],
                       current_photo, current_photo2))
            conn.commit()
            conn.close()
            sg.popup("Property added successfully!")
            current_photo = None
            current_photo2 = None
            window["prop_name"].update("")
            window["prop_location"].update("")
            window["prop_price"].update("\u20b1")
            window["prop_status"].update("")
            window["prop_client_name"].update("")
            window["prop_client_contact"].update("+63 ")
            window["prop_client_email"].update("")
            window["prop_client_address"].update("")
            window["photo_display"].update(data=None)
            window["photo_display2"].update(data=None)
    window.close()

def dashboard():
    window = sg.Window("Sales Management System", create_dashboard_layout(), resizable=False, element_justification='c', size=(1150, 750))
    search_results = []
    selected_prop_id = None
    due = check_due_payments()
    
    if due:
        window["due_alert"].update(f"  {len(due)} due payment(s) \u2014 go to Payments tab")
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Logout"):
            break
        elif event == "Search":
            keyword = values["search_keyword"].strip()
            if not keyword:
                sg.popup("Enter a keyword to search")
                continue
            search_results = search_properties(keyword)
            if search_results:
                display = [[r[0], r[1] or "", r[2] or "", f"\u20b1{r[3]:,.2f}", r[4] or "", r[5] or ""] for r in search_results]
                window["prop_search_results"].update(values=display, visible=True)
            else:
                window["prop_search_results"].update(values=[], visible=False)
                sg.popup(f"No properties found matching '{keyword}'")
        elif isinstance(event, tuple) and event[0] == "prop_search_results":
            if len(event) > 2 and event[2] is not None and isinstance(event[2], tuple) and event[2][0] is not None:
                row_idx = event[2][0]
                if row_idx < len(search_results):
                    selected = search_results[row_idx]
                    selected_prop_id = selected[0]
                    prop = get_property_by_id(selected[0])
                    if prop:
                        try:
                            price_str = f"\u20b1{float(prop['price']):,.2f}" if prop['price'] else "--"
                        except (ValueError, TypeError):
                            price_str = "--"
                        window["-DETAIL_HEADER-"].update(visible=True)
                        window["-DETAIL_FIELDS-"].update(visible=True)
                        window["-DETAIL_NAME-"].update(prop["name"] or "")
                        window["-DETAIL_LOCATION-"].update(prop["location"] or "")
                        window["-DETAIL_PRICE-"].update(price_str)
                        window["-DETAIL_STATUS-"].update(prop["status"] or "")
                        window["-DETAIL_CLIENT-"].update(prop["client_name"] or "")
                        window["-DETAIL_CONTACT-"].update(prop["client_contact"] or "")
                        window["-DETAIL_EMAIL-"].update(prop["client_email"] or "")
                        window["-DETAIL_ADDRESS-"].update(prop["client_address"] or "")
                        if prop["photo"]:
                            resized = resize_image_for_display(prop["photo"])
                            window["-DETAIL_PHOTO1-"].update(data=resized)
                        else:
                            window["-DETAIL_PHOTO1-"].update(data=None)
                        if prop["photo2"]:
                            resized2 = resize_image_for_display(prop["photo2"])
                            window["-DETAIL_PHOTO2-"].update(data=resized2)
                        else:
                            window["-DETAIL_PHOTO2-"].update(data=None)
                        window["-DETAIL_PHOTOS-"].update(visible=True)
        elif event == "Manage Properties":
            manage_properties_window(selected_prop_id)
        elif event == "Add Property":
            add_property_window()
        elif event == "Add Payment":
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            c.execute("INSERT INTO payments (id, property_id, amount, date, status) VALUES (?, ?, ?, ?, ?)",
                      (next_id("payments", "PAY"), values["pay_property_id"], values["pay_amount"], values["pay_date"], values["pay_status"]))
            conn.commit()
            conn.close()
            sg.popup("Payment added successfully!")
        elif event == "View Payments":
            conn = sqlite3.connect("primarius.db")
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
                sg.popup_scrolled("DUE PAYMENTS", *[f"{r[0]} | {r[1]} | {r[5]} |  #{r[2]}  | Due: {r[3]}  |  \u20b1{r[4]:,.2f}" for r in due])
            else:
                sg.popup("No due payments!")
        elif event == "Generate Report":
            conn = sqlite3.connect("primarius.db")
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
                c.execute("""SELECT properties.client_name, SUM(payments.amount), MAX(payments.date), COUNT(payments.id)
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             WHERE properties.client_name IS NOT NULL
                             GROUP BY properties.client_name
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
