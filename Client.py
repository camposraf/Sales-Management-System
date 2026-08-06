## Sales Management System by Valkyrie Softworks (est. 2024) ##
import sqlite3
import PySimpleGUI as sg
import hashlib
from datetime import datetime
import calendar
from PIL import Image
import io
import re

sg.theme("DarkBlue")

# Generates the next available ID for a given table and prefix, considering deleted IDs
def next_id(table, prefix):
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS deleted_ids(id TEXT PRIMARY KEY)""")
    c.execute(f"SELECT id FROM {table} WHERE id LIKE '{prefix}-%'")
    rows = c.fetchall()
    nums = [int(r[0].split("-")[1]) for r in rows if r[0] and "-" in r[0]]
    n = max(nums) + 1 if nums else 1
    while True:
        candidate = f"{prefix}-{n:03d}"
        c.execute("SELECT id FROM deleted_ids WHERE id=?", (candidate,))
        if c.fetchone() is None:
            break
        n += 1
    conn.close()
    return f"{prefix}-{n:03d}"

# Resizes uploaded photos for display in the GUI, maintaining aspect ratio and limiting dimensions
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

# Search functions for properties and payments based on a keyword, returning matching rows from the database
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

def search_payments(keyword):
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    q = f"%{keyword}%"
    c.execute("""SELECT id, property_id, amount, date, status 
                 FROM payments 
                 WHERE id LIKE ? OR property_id LIKE ? OR status LIKE ? OR date LIKE ?""",
              (q, q, q, q))
    rows = c.fetchall()
    conn.close()
    return rows

# Fetches property details by ID, returning a dictionary of property attributes or None if not found
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

#Formats contact number into +63 country code
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

# Layout for the property details popup, displaying property attributes and photos in a modal window
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

# Main dashboard layout with tabs for properties, payments, and reports, including search and action buttons
def create_dashboard_layout():
    prop_tab = sg.Tab("Properties", [
        [sg.Push(), sg.Button("See All Properties", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
         sg.Button("Add Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
        [sg.Text("Search:", font=("Helvetica", 16)), sg.Input(key="search_keyword", font=("Helvetica", 16), size=(30,1), expand_x=True),
         sg.Button("Search", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14))],
        [sg.pin(sg.Column([
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
        ], key="-PROP_TABLE_WRAP-", expand_x=True, pad=(0,0)), expand_x=True)],
        [sg.Push(), sg.Button("Manage Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
         sg.Button("Delete Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
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
        [sg.Push(), sg.Button("See All Payments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
         sg.Button("New Payment / Plan", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
        [sg.Text("Search:", font=("Helvetica", 16)), sg.Input(key="pay_search_keyword", font=("Helvetica", 16), size=(30,1), expand_x=True),
         sg.Button("Search", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14), key="Pay Search")],
        [sg.pin(sg.Column([
            [sg.Table(
                values=[["", "", "", "", ""]],
                headings=["ID", "Property ID", "Amount", "Date", "Status"],
                key="pay_search_results",
                font=("Helvetica", 12),
                justification="left",
                num_rows=6,
                auto_size_columns=True,
                visible=False,
                enable_click_events=True,
                expand_x=True
            )],
        ], key="-PAY_TABLE_WRAP-", expand_x=True, pad=(0,0)), expand_x=True)],
        [sg.pin(sg.Column([
            [sg.Text("DUE PAYMENTS", font=("Helvetica", 14, "bold"), visible=False, key="-DUE_HEADER-")],
            [sg.Table(
                values=[["", "", "", "", "", "", ""]],
                headings=["ID", "Client", "Property", "#", "Due Date", "Amount", "Status"],
                key="due_pay_results",
                font=("Helvetica", 12),
                justification="left",
                num_rows=5,
                auto_size_columns=True,
                visible=False,
                enable_click_events=True,
                expand_x=True
            )],
        ], key="-DUE_WRAP-", expand_x=True, pad=(0,0)), expand_x=True)],
        [sg.Push(), sg.Button("View Installments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
         sg.Button("Due Payments", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
        [sg.HorizontalSeparator()],
        [sg.pin(sg.Column([
            [sg.Text("NEW PAYMENT / PLAN", font=("Helvetica", 14, "bold"), visible=False, key="-PAY_HEADER-")],
            [sg.Column([
                [sg.Text("Mode:", font=("Helvetica", 12), size=(12,1), pad=(0, 6)),
                 sg.Combo(["Select Mode", "Record Payment", "Setup Plan"], key="pay_mode", default_value="Select Mode", enable_events=True, font=("Helvetica", 12), size=(22,1), readonly=True, pad=(5, 6))],
                [sg.Text("Property ID:", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Input(key="pay_property_id", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
            ], visible=False, key="-PAY_FIELDS-")],
            [sg.pin(sg.Column([
                [sg.Text("Amount:", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Input(key="pay_amount", default_text="\u20b1", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
                [sg.Text("Date (YYYY-MM-DD):", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Input(key="pay_date", font=("Helvetica", 12), size=(20,1), pad=(5, 6)),
                 sg.CalendarButton("Pick Date", target="pay_date", format="%Y-%m-%d", font=("Helvetica", 12), button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, pad=(5, 6))],
                [sg.Text("Status:", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Combo(["Paid", "Pending", "Overdue"], key="pay_status", font=("Helvetica", 12), size=(22,1), readonly=True, pad=(5, 6))],
            ], visible=False, key="-PAY_PAYMENT_FIELDS-"))],
            [sg.pin(sg.Column([
                [sg.Text("Total Amount:", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Input(key="pay_total_amount", default_text="\u20b1", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
                [sg.Text("Down Payment:", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Input(key="pay_down_payment", default_text="\u20b1", font=("Helvetica", 12), size=(25,1), pad=(5, 6))],
                [sg.Text("Frequency:", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Combo(["6 Months", "12 Months"], key="pay_frequency", default_value="12 Months", font=("Helvetica", 12), size=(22,1), readonly=True, pad=(5, 6))],
                [sg.Text("Start Date (YYYY-MM-DD):", font=("Helvetica", 12), size=(12,1), pad=(0, 6)), sg.Input(key="pay_start_date", font=("Helvetica", 12), size=(20,1), pad=(5, 6)),
                 sg.CalendarButton("Pick Date", target="pay_start_date", format="%Y-%m-%d", font=("Helvetica", 12), button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, pad=(5, 6))],
            ], visible=False, key="-PAY_PLAN_FIELDS-"))],
            [sg.Push(), sg.Button("Save Payment", key="save_pay_btn", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
        ], key="-PAY_FORM_WRAP-", expand_x=True, pad=(0,0)), expand_x=True)],
    ])
    rpt_tab = sg.Tab("Reports", [
        [sg.Push(),
         sg.Column([
            [sg.Text("TOTAL SALES", font=("Helvetica", 12), text_color="gray", justification="center")],
            [sg.Text("\u20b10.00", key="stat_sales", font=("Helvetica", 22, "bold"), justification="center")],
         ], pad=(15, 15), element_justification="c"),
         sg.Column([
            [sg.Text("PAYMENTS", font=("Helvetica", 12), text_color="gray", justification="center")],
            [sg.Text("0", key="stat_pay", font=("Helvetica", 22, "bold"), justification="center")],
         ], pad=(15, 15), element_justification="c"),
         sg.Column([
            [sg.Text("OVERDUE", font=("Helvetica", 12), text_color="gray", justification="center")],
            [sg.Text("0", key="stat_overdue", font=("Helvetica", 22, "bold"), justification="center")],
         ], pad=(15, 15), element_justification="c"),
         sg.Push()],
        [sg.HorizontalSeparator()],
        [sg.Text("Report Type:", font=("Helvetica", 16)),
         sg.Combo(["Overdue Payments", "Payments by Client", "Payments by Property"], key="report_type", default_value="Overdue Payments", enable_events=True, font=("Helvetica", 16), size=(25, 1), readonly=True),
         sg.Button("Generate Report", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 16))],
        [sg.pin(sg.Table(
            values=[["", "", "", ""]],
            headings=["Item", "Amount", "Date", "Payments"],
            key="report_results",
            font=("Helvetica", 12),
            justification="center",
            num_rows=12,
            auto_size_columns=True,
            visible=False,
            enable_click_events=True,
            expand_x=True
        ), expand_x=True)],
        [sg.pin(sg.Multiline(key="report_output", default_text="No report generated yet. Select a report type and click Generate Report.", size=(150, 8), font=("Consolas", 11), disabled=True, autoscroll=True), expand_x=True)],
        [sg.Push(), sg.Button("Export Report", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
    ])
    return [
        [sg.Text("Sales Management System", font=("Helvetica", 20), justification="center")],
        [sg.Text("", key="due_alert", font=("Helvetica", 16), text_color="red", justification="center")],
        [sg.TabGroup([[prop_tab, pay_tab, rpt_tab]], tab_location='lefttab', font=("Helvetica", 14), expand_x=True, size=(1100, 650))],
        [sg.Push(), sg.Button("Logout", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 20)), sg.Push()],
    ]

# Layout for the property management interface, allowing users to search, view, and update property details, including client information and photos
def create_property_management_layout():
    return [
        [sg.Text("Manage Property", font=("Helvetica", 20), justification="center", pad=(0, (10, 15)))],
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

# Layout for the login interface
def create_login_layout():
    card = [
        [sg.Text("Primarius Realty Development", font=("Helvetica", 22, "bold"), justification="center")],
        [sg.Text("Sales Management System", font=("Helvetica", 13), text_color="white", justification="center")],
        [sg.HorizontalSeparator(pad=(0, 14))],
        [sg.Text("Email", font=("Helvetica", 12), text_color="white", pad=(0, (0, 4)))],
        [sg.Input(key="email", font=("Helvetica", 14), size=(34, 1), pad=(0, (0, 12)))],
        [sg.Text("Password", font=("Helvetica", 12), text_color="white", pad=(0, (0, 4)))],
        [sg.Input(key="password", password_char="*", font=("Helvetica", 14), size=(34, 1), pad=(0, (0, 16)))],
        [sg.Button("SIGN IN", key="Login", button_color=("white", "#2563eb"), border_width=0, font=("Helvetica", 14, "bold"), size=(36, 1), pad=(0, (0, 10)))],
        [sg.HorizontalSeparator(pad=(0, 12))],
        [sg.Text("New to the system?", font=("Helvetica", 12), text_color="white", justification="center")],
        [sg.Button("Create an Account", key="Register", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 13), pad=(0, (4, 6)))],
        [sg.Push(), sg.Button("Exit", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 13)), sg.Push()],
    ]
    return [
        [sg.Push(),
         sg.Frame("", card, border_width=2, relief=sg.RELIEF_GROOVE, element_justification="c", pad=(25, 25)),
         sg.Push()],
    ]

# Layout for the registration interface
def create_registration_layout():
    card = [
        [sg.Text("Create Account", font=("Helvetica", 22, "bold"), justification="center")],
        [sg.Text("Register to the Sales Management System", font=("Helvetica", 13), text_color="white", justification="center")],
        [sg.HorizontalSeparator(pad=(0, 14))],
        [sg.Text("Email", font=("Helvetica", 12), text_color="white", pad=(0, (0, 4)))],
        [sg.Input(key="email", font=("Helvetica", 14), size=(34, 1), pad=(0, (0, 12)))],
        [sg.Text("Password", font=("Helvetica", 12), text_color="white", pad=(0, (0, 4)))],
        [sg.Input(key="password", password_char="*", font=("Helvetica", 14), size=(34, 1), pad=(0, (0, 12)))],
        [sg.Text("Confirm Password", font=("Helvetica", 12), text_color="white", pad=(0, (0, 4)))],
        [sg.Input(key="confirm_password", password_char="*", font=("Helvetica", 14), size=(34, 1), pad=(0, (0, 16)))],
        [sg.Button("REGISTER", key="Register", button_color=("white", "#2563eb"), border_width=0, font=("Helvetica", 14, "bold"), size=(36, 1), pad=(0, (0, 10)))],
        [sg.HorizontalSeparator(pad=(0, 12))],
        [sg.Text("Already have an account?", font=("Helvetica", 12), text_color="white", justification="center")],
        [sg.Button("Back to Login", key="Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 13), pad=(0, (4, 6)))],
    ]
    return [
        [sg.Push(),
         sg.Frame("", card, border_width=2, relief=sg.RELIEF_GROOVE, element_justification="c", pad=(25, 25)),
         sg.Push()],
    ]

# Layout for the payment plan interface
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
            [sg.Text("Start Date (YYYY-MM-DD)", font=("Helvetica", 20), size=(20,1)), sg.Input(key="start_date", font=("Helvetica", 20), size=(15,1)),
             sg.CalendarButton("Pick Date", target="start_date", format="%Y-%m-%d", font=("Helvetica", 20), button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0)],
            [sg.Text("", size=(1,1))],
            [sg.Text("", key="calc_result", font=("Helvetica", 16), text_color="yellow")],
        ])],
    ]

# Layout for the installments interface
def create_installments_layout():
    return [
        [sg.Text("Installments", font=("Helvetica", 20), justification="center", pad=(0, (10, 15)))],
        [sg.Push(), sg.Button("Show All Pending", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
         sg.Button("Show All", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
         sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
        [sg.Table(
            values=[["", "", "", "", "", "", ""]],
            headings=["ID", "Client", "Property", "#", "Due Date", "Amount", "Status"],
            key="ins_results",
            font=("Helvetica", 12),
            justification="left",
            num_rows=8,
            auto_size_columns=True,
            visible=False,
            enable_click_events=True,
            expand_x=True
        )],
        [sg.HorizontalSeparator()],
        [sg.Column([
            [sg.Text("Installment ID:", font=("Helvetica", 12), size=(14,1), pad=(0, 6)), sg.Text("", key="ins_id", font=("Helvetica", 12, "bold"), size=(22,1), pad=(5, 6)),
             sg.Text("Client Name:", font=("Helvetica", 12), size=(14,1), pad=(0, 6)), sg.Text("", key="ins_client", font=("Helvetica", 12, "bold"), size=(25,1), pad=(5, 6))],
            [sg.Text("Property Name:", font=("Helvetica", 12), size=(14,1), pad=(0, 6)), sg.Text("", key="ins_property", font=("Helvetica", 12, "bold"), size=(22,1), pad=(5, 6)),
             sg.Text("Installment #:", font=("Helvetica", 12), size=(14,1), pad=(0, 6)), sg.Text("", key="ins_num", font=("Helvetica", 12, "bold"), size=(25,1), pad=(5, 6))],
            [sg.Text("Due Date:", font=("Helvetica", 12), size=(14,1), pad=(0, 6)), sg.Text("", key="ins_due", font=("Helvetica", 12, "bold"), size=(22,1), pad=(5, 6)),
             sg.Text("Amount:", font=("Helvetica", 12), size=(14,1), pad=(0, 6)), sg.Text("", key="ins_amount", font=("Helvetica", 12, "bold"), size=(25,1), pad=(5, 6))],
            [sg.Text("Status:", font=("Helvetica", 12), size=(14,1), pad=(0, 6)), sg.Text("", key="ins_status", font=("Helvetica", 12, "bold"), size=(22,1), pad=(5, 6))],
        ], visible=False, key="-INS_DETAILS-")],
        [sg.Push(), sg.Button("Record Payment", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
    ]

# Database initialization
def init_db():
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              first_login INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE,
              password TEXT,
              role TEXT)""")
    try:
        em_cols = [r[1] for r in c.execute("PRAGMA table_info(employees)").fetchall()]
        if "username" in em_cols and "email" not in em_cols:
                c.execute("ALTER TABLE employees RENAME COLUMN username TO email")
    except sqlite3.OperationalError:
        pass
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
    c.execute("""CREATE TABLE IF NOT EXISTS deleted_ids(
        id TEXT PRIMARY KEY
    )""")
    conn.commit()
    conn.close()

# Password hashing and user authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None

def login(email, password):
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE email=? AND password=?",
              (email, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result

# Check due payments 
def check_due_payments():
    conn = sqlite3.connect("primarius.db")
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""SELECT pi.id, p.client_name, pi.installment_number, pi.due_date, pi.amount, p.name, pi.property_id
                 FROM payment_installments pi
                 JOIN properties p ON pi.property_id = p.id
                 WHERE pi.due_date <= ? AND pi.status = 'Pending'""", (today,))
    due = c.fetchall()
    conn.close()
    return due

# Create installments for a payment plan
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

# User registration window
def register_window():
    window = sg.Window("Register", create_registration_layout(), resizable=True, element_justification='c', size=(520, 540))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Register":
            email_val = values["email"].strip()
            if not is_valid_email(email_val):
                sg.popup("Please enter a valid email address.")
                continue
            if not values["password"]:
                sg.popup("Password is required.")
                continue
            if values["password"] != values["confirm_password"]:
                sg.popup("Passwords do not match. Please try again.")
                continue
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            try:
                c.execute("INSERT INTO employees (email, password) VALUES (?, ?)",
                          (email_val, hash_password(values["password"])))
                conn.commit()
                sg.popup("Registration successful! Please log in.")
                window.close()
                break
            except sqlite3.IntegrityError:
                sg.popup("Email already registered. Please use a different email address.")
            finally:
                conn.close()
    window.close()

# Payment plan creation window
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

# Installments management window
def installments_window():
    window = sg.Window("Installments", create_installments_layout(), resizable=True, element_justification='c', size=(900, 600), finalize=True)
    ins_cache = []
    selected_ins_id = None
    filter_pending = False
    today = datetime.now().strftime("%Y-%m-%d")
    sort_col = None
    sort_asc = True
    def apply_sort():
        nonlocal ins_cache, sort_col, sort_asc
        if sort_col is None or not ins_cache:
            return
        def key_fn(r):
            v = r[sort_col]
            return (v is None, "" if v is None else v)
        ins_cache.sort(key=key_fn, reverse=not sort_asc)
        display = [[r[0], r[1] or "", r[2] or "", r[3], r[4] or "", f"\u20b1{float(r[5]):,.2f}" if r[5] else "--", status_display(r)] for r in ins_cache]
        window["ins_results"].update(values=display, visible=True)
    def status_display(r):
        st = r[6] or ""
        if st == "Pending" and r[4] and r[4] < today:
            st = "OVERDUE"
        return st
    def load_installments(pending_only):
        nonlocal ins_cache, sort_col, sort_asc
        conn = sqlite3.connect("primarius.db")
        c = conn.cursor()
        if pending_only:
            c.execute("""SELECT pi.id, p.client_name, p.name, pi.installment_number, pi.due_date, pi.amount, pi.status
                         FROM payment_installments pi
                         JOIN properties p ON pi.property_id = p.id
                         WHERE pi.status = 'Pending' ORDER BY pi.due_date""")
        else:
            c.execute("""SELECT pi.id, p.client_name, p.name, pi.installment_number, pi.due_date, pi.amount, pi.status
                         FROM payment_installments pi
                         JOIN properties p ON pi.property_id = p.id
                         ORDER BY pi.due_date""")
        ins_cache = c.fetchall()
        conn.close()
        sort_col = None
        sort_asc = True
        if ins_cache:
            display = [[r[0], r[1] or "", r[2] or "", r[3], r[4] or "", f"\u20b1{float(r[5]):,.2f}" if r[5] else "--", status_display(r)] for r in ins_cache]
            window["ins_results"].update(values=display, visible=True)
        else:
            window["ins_results"].update(values=[], visible=False)
            window["-INS_DETAILS-"].update(visible=False)
            sg.popup("No installments found.")
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Back"):
            break
        if event == "Show All Pending":
            filter_pending = True
            load_installments(True)
        elif event == "Show All":
            filter_pending = False
            load_installments(False)
        elif isinstance(event, tuple) and event[0] == "ins_results":
            if len(event) > 2 and event[2] is not None and isinstance(event[2], tuple):
                row_idx, col_idx = event[2][0], event[2][1]
                if row_idx is None or row_idx < 0:
                    if col_idx is not None and col_idx >= 0:
                        if col_idx == sort_col:
                            sort_asc = not sort_asc
                        else:
                            sort_col = col_idx
                            sort_asc = True
                        apply_sort()
                elif row_idx < len(ins_cache):
                    sel = ins_cache[row_idx]
                    selected_ins_id = sel[0]
                    window["-INS_DETAILS-"].update(visible=True)
                    window["ins_id"].update(sel[0])
                    window["ins_client"].update(sel[1] or "")
                    window["ins_property"].update(sel[2] or "")
                    window["ins_num"].update(sel[3])
                    window["ins_due"].update(sel[4] or "")
                    window["ins_amount"].update(f"\u20b1{float(sel[5]):,.2f}" if sel[5] else "--")
                    status = sel[6] or ""
                    if sel[6] == "Pending" and sel[4] and sel[4] < today:
                        status = "OVERDUE"
                    elif sel[6] == "Pending" and sel[4] and sel[4] == today:
                        status = "DUE TODAY"
                    window["ins_status"].update(status)
        elif event == "Record Payment":
            if not selected_ins_id:
                sg.popup("Select an installment from the table first.")
            else:
                try:
                    conn = sqlite3.connect("primarius.db")
                    c = conn.cursor()
                    c.execute("SELECT property_id, amount FROM payment_installments WHERE id=?",
                              (selected_ins_id,))
                    row = c.fetchone()
                    if not row:
                        sg.popup("No installment found with that ID")
                    else:
                        prop_id, amount = row
                        c.execute("""UPDATE payment_installments SET status='Paid', paid_date=? WHERE id=?""",
                                  (today, selected_ins_id))
                        pay_id = next_id("payments", "PAY")
                        c.execute("INSERT INTO payments (id, property_id, amount, date, status) VALUES (?, ?, ?, ?, ?)",
                                  (pay_id, prop_id, amount, today, "Paid"))
                        conn.commit()
                        sg.popup("Installment marked as paid! Payment recorded in ledger.")
                        selected_ins_id = None
                        window["-INS_DETAILS-"].update(visible=False)
                        load_installments(filter_pending)
                    conn.close()
                except Exception as e:
                    sg.popup(f"Error: {e}")
    window.close()

# User login window
def login_window():
    window = sg.Window("Login", create_login_layout(), resizable=True, element_justification='c', size=(520, 500))
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        if event == "Register":
            register_window()
        if event == "Login":
            user = login(values["email"].strip(), values["password"])
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

# Manage properties window
def manage_properties_window(prop_id=None):
    window = sg.Window("Manage Property", create_property_management_layout(), resizable=False, element_justification='c', size=(950, 750), finalize=True)
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

# Add property window
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
        [sg.Push(), sg.Button("Upload Photos", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)),
                 sg.Button("Back", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14))],
        [sg.Image(key="photo_display", size=(200, 200)),
         sg.Image(key="photo_display2", size=(200, 200))],
        [sg.Push(), sg.Button("Add Property", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0, font=("Helvetica", 14)), sg.Push()],
        
    ]

# Add property window function
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

# Main dashboard window
def dashboard():
    window = sg.Window("Sales Management System", create_dashboard_layout(), resizable=False, element_justification='c', size=(1150, 750), finalize=True)
    search_results = []
    pay_search_cache = []
    due_pay_cache = []
    pending_due_ins_id = None
    selected_prop_id = None
    report_cache = []
    report_sort_col = None
    report_sort_asc = True
    report_title = ""
    def set_pay_mode(mode):
        window["pay_mode"].update(mode)
        if mode == "Record Payment":
            window["-PAY_PAYMENT_FIELDS-"].update(visible=True)
            window["-PAY_PLAN_FIELDS-"].update(visible=False)
            window["save_pay_btn"].update("Save Payment", disabled=False)
        elif mode == "Setup Plan":
            window["-PAY_PAYMENT_FIELDS-"].update(visible=False)
            window["-PAY_PLAN_FIELDS-"].update(visible=True)
            window["save_pay_btn"].update("Save Plan", disabled=False)
        else:
            window["-PAY_PAYMENT_FIELDS-"].update(visible=False)
            window["-PAY_PLAN_FIELDS-"].update(visible=False)
            window["save_pay_btn"].update(disabled=True)
    def refresh_due_alert():
        due = check_due_payments()
        if due:
            window["due_alert"].update(f"  {len(due)} due payment(s) \u2014 go to Payments tab")
        else:
            window["due_alert"].update("")
    def refresh_report_stats():
        conn = sqlite3.connect("primarius.db")
        c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM payments")
        total, count = c.fetchone()
        conn.close()
        window["stat_sales"].update(f"\u20b1{float(total or 0):,.2f}")
        window["stat_pay"].update(str(count))
        window["stat_overdue"].update(str(len(check_due_payments())))
    def refresh_report_table():
        nonlocal report_cache, report_sort_col, report_sort_asc, report_title
        if not report_cache:
            window["report_results"].update(values=[], visible=False)
            window["report_output"].update("No report generated yet. Select a report type and click Generate Report.")
            return
        if report_sort_col is not None:
            def key_fn(r):
                v = r[report_sort_col]
                if isinstance(v, (int, float)):
                    return (0, 0 if v is None else v)
                return (1, "" if v is None else str(v))
            report_cache.sort(key=key_fn, reverse=not report_sort_asc)
        display = [[r[0], f"\u20b1{float(r[1]):,.2f}" if r[1] is not None else "--", r[2] or "", str(r[3]) if r[3] else ""] for r in report_cache]
        window["report_results"].update(values=display, visible=True)
        window["report_output"].update(visible=False)
        lines = [f"{report_title}  (generated {datetime.now().strftime('%Y-%m-%d %H:%M')})"]
        lines.append("=" * 55)
        lines.append(f"{'Item':<20}  {'Amount':>10}  {'Date':<12}  {'Payments':>8}")
        lines.append("-" * 55)
        for r in report_cache:
            amt = f"\u20b1{float(r[1]):,.2f}" if r[1] is not None else "--"
            lines.append(f"{str(r[0]):<20}  {amt:>10}  {str(r[2] or ''):<12}  {str(r[3] if r[3] else ''):>8}")
        window["report_output"].update("\n".join(lines))
    refresh_due_alert()
    refresh_report_stats()
    set_pay_mode("Select Mode")
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Logout"):
            break
        elif event == "See All Properties":
            if window["-PROP_TABLE_WRAP-"].visible:
                window["-PROP_TABLE_WRAP-"].update(visible=False)
            else:
                search_results = search_properties("")
                if search_results:
                    display = [[r[0], r[1] or "", r[2] or "", f"\u20b1{float(r[3]):,.2f}" if r[3] else "--", r[4] or "", r[5] or ""] for r in search_results]
                    window["prop_search_results"].update(values=display, visible=True)
                    window["-PROP_TABLE_WRAP-"].update(visible=True)
                else:
                    window["prop_search_results"].update(values=[], visible=False)
                    sg.popup("No properties found.")
        elif event == "Search":
            keyword = values["search_keyword"].strip()
            if not keyword:
                sg.popup("Enter a keyword to search")
                continue
            search_results = search_properties(keyword)
            if search_results:
                display = [[r[0], r[1] or "", r[2] or "", f"\u20b1{r[3]:,.2f}", r[4] or "", r[5] or ""] for r in search_results]
                window["prop_search_results"].update(values=display, visible=True)
                window["-PROP_TABLE_WRAP-"].update(visible=True)
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
        elif event == "Manage Property":
            manage_properties_window(selected_prop_id)
        elif event == "Delete Property":
            if not selected_prop_id:
                sg.popup("No property selected! Search and click a property first.")
            else:
                confirm = sg.popup_yes_no(f"Delete property {selected_prop_id} and all related records?")
                if confirm == "Yes":
                    conn = sqlite3.connect("primarius.db")
                    c = conn.cursor()
                    c.execute("DELETE FROM payment_installments WHERE property_id=?", (selected_prop_id,))
                    c.execute("DELETE FROM payment_plans WHERE property_id=?", (selected_prop_id,))
                    c.execute("DELETE FROM payments WHERE property_id=?", (selected_prop_id,))
                    c.execute("DELETE FROM properties WHERE id=?", (selected_prop_id,))
                    c.execute("INSERT OR IGNORE INTO deleted_ids (id) VALUES (?)", (selected_prop_id,))
                    conn.commit()
                    conn.close()
                    sg.popup("Property deleted successfully!")
                    search_results = []
                    window["-PROP_TABLE_WRAP-"].update(visible=False)
                    window["-DETAIL_HEADER-"].update(visible=False)
                    window["-DETAIL_FIELDS-"].update(visible=False)
                    window["-DETAIL_PHOTOS-"].update(visible=False)
        elif event == "Add Property":
            add_property_window()
        elif event == "See All Payments":
            if window["-PAY_TABLE_WRAP-"].visible:
                window["-PAY_TABLE_WRAP-"].update(visible=False)
            else:
                pay_search_cache = search_payments("")
                if pay_search_cache:
                    display = [[r[0], r[1] or "", f"\u20b1{float(r[2]):,.2f}" if r[2] else "--", r[3] or "", r[4] or ""] for r in pay_search_cache]
                    window["pay_search_results"].update(values=display, visible=True)
                    window["-PAY_TABLE_WRAP-"].update(visible=True)
                else:
                    window["pay_search_results"].update(values=[], visible=False)
                    sg.popup("No payments found.")
        elif event == "Pay Search":
            keyword = values["pay_search_keyword"].strip()
            if not keyword:
                pay_search_cache = search_payments("")
            else:
                pay_search_cache = search_payments(keyword)
            if pay_search_cache:
                display = [[r[0], r[1] or "", f"\u20b1{float(r[2]):,.2f}" if r[2] else "--", r[3] or "", r[4] or ""] for r in pay_search_cache]
                window["pay_search_results"].update(values=display, visible=True)
                window["-PAY_TABLE_WRAP-"].update(visible=True)
            else:
                window["pay_search_results"].update(values=[], visible=False)
                sg.popup(f"No payments found matching '{keyword}'")
        elif event == "New Payment / Plan":
            if window["-PAY_FORM_WRAP-"].visible:
                window["-PAY_FORM_WRAP-"].update(visible=False)
            else:
                window["-PAY_FORM_WRAP-"].update(visible=True)
                window["-PAY_HEADER-"].update(visible=True)
                window["-PAY_FIELDS-"].update(visible=True)
                set_pay_mode("Select Mode")
        elif event == "pay_mode":
            set_pay_mode(values["pay_mode"])
        elif event == "save_pay_btn":
            prop_id = values["pay_property_id"].strip()
            if values["pay_mode"] == "Select Mode":
                sg.popup("Select a mode first.")
                continue
            if not prop_id:
                sg.popup("Enter a Property ID")
                continue
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            c.execute("SELECT id FROM properties WHERE id=?", (prop_id,))
            if not c.fetchone():
                conn.close()
                sg.popup(f"Property ID '{prop_id}' not found.")
                continue
            if values["pay_mode"] == "Record Payment":
                amount_val = values["pay_amount"].replace("\u20b1", "").replace(",", "").strip()
                if not amount_val:
                    conn.close()
                    sg.popup("Enter an amount")
                    continue
                pay_date = values["pay_date"].strip() or datetime.now().strftime("%Y-%m-%d")
                status = values["pay_status"] or "Paid"
                pay_id = next_id("payments", "PAY")
                c.execute("INSERT INTO payments (id, property_id, amount, date, status) VALUES (?, ?, ?, ?, ?)",
                          (pay_id, prop_id, float(amount_val), pay_date, status))
                if pending_due_ins_id:
                    c.execute("""UPDATE payment_installments SET status='Paid', paid_date=? WHERE id=?""",
                              (pay_date, pending_due_ins_id))
                conn.commit()
                conn.close()
                if pending_due_ins_id:
                    sg.popup("Payment completed! Installment marked as paid.")
                    pending_due_ins_id = None
                else:
                    sg.popup(f"Payment {pay_id} recorded!")
            else:
                try:
                    total = float(values["pay_total_amount"].replace("\u20b1", "").replace(",", "").strip())
                    down = float(values["pay_down_payment"].replace("\u20b1", "").replace(",", "").strip())
                    freq = values["pay_frequency"] or "12 Months"
                    num = 6 if freq == "6 Months" else 12
                    remaining = total - down
                    installment_amount = round(remaining / num, 2)
                    start_date = values["pay_start_date"].strip()
                    plan_id = next_id("payment_plans", "PLN")
                    c.execute("""INSERT INTO payment_plans (id, property_id, total_amount, down_payment, installment_amount, total_installments, frequency, start_date)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                              (plan_id, prop_id, total, down, installment_amount, num, freq, start_date))
                    conn.commit()
                    conn.close()
                    create_installments(plan_id, prop_id, num, installment_amount, start_date, "Monthly")
                    sg.popup(f"Payment plan {plan_id} created! {num} monthly installments of \u20b1{installment_amount:,.2f} each.")
                except (ValueError, ZeroDivisionError):
                    conn.close()
                    sg.popup("Enter valid numbers for Total, Down Payment, and Start Date (YYYY-MM-DD).")
                    continue
            window["pay_property_id"].update("")
            window["pay_amount"].update("\u20b1")
            window["pay_date"].update("")
            window["pay_status"].update("")
            window["pay_total_amount"].update("\u20b1")
            window["pay_down_payment"].update("\u20b1")
            window["pay_start_date"].update("")
            window["pay_frequency"].update("12 Months")
            set_pay_mode("Select Mode")
            refresh_due_alert()
            if window["-DUE_WRAP-"].visible:
                due_pay_cache = check_due_payments()
                if due_pay_cache:
                    display = [[r[0], r[1] or "", r[5] or "", r[2], r[3] or "", f"\u20b1{float(r[4]):,.2f}" if r[4] else "--", "Overdue"] for r in due_pay_cache]
                    window["due_pay_results"].update(values=display, visible=True)
                    window["-DUE_HEADER-"].update(visible=True)
                else:
                    window["-DUE_WRAP-"].update(visible=False)
        elif isinstance(event, tuple) and event[0] == "pay_search_results":
            if len(event) > 2 and event[2] is not None and isinstance(event[2], tuple) and event[2][0] is not None:
                row_idx = event[2][0]
                if row_idx < len(pay_search_cache):
                    selected_pay = pay_search_cache[row_idx]
                    window["-PAY_FORM_WRAP-"].update(visible=True)
                    window["-PAY_HEADER-"].update(visible=True)
                    window["-PAY_FIELDS-"].update(visible=True)
                    set_pay_mode("Record Payment")
                    window["pay_property_id"].update(selected_pay[1] or "")
                    try:
                        pay_amount_str = f"\u20b1{float(selected_pay[2]):,.2f}" if selected_pay[2] else "\u20b1"
                    except (ValueError, TypeError):
                        pay_amount_str = "\u20b1"
                    window["pay_amount"].update(pay_amount_str)
                    window["pay_date"].update(selected_pay[3] or "")
                    window["pay_status"].update(selected_pay[4] or "")
        elif event == "View Payments":
            pay_search_cache = search_payments("")
            if pay_search_cache:
                display = [[r[0], r[1] or "", f"\u20b1{float(r[2]):,.2f}" if r[2] else "--", r[3] or "", r[4] or ""] for r in pay_search_cache]
                window["pay_search_results"].update(values=display, visible=True)
            else:
                window["pay_search_results"].update(values=[], visible=False)
                sg.popup("No payments found.")
        elif event == "View Installments":
            installments_window()
            refresh_due_alert()
            if window["-DUE_WRAP-"].visible:
                due_pay_cache = check_due_payments()
                if due_pay_cache:
                    display = [[r[0], r[1] or "", r[5] or "", r[2], r[3] or "", f"\u20b1{float(r[4]):,.2f}" if r[4] else "--", "Overdue"] for r in due_pay_cache]
                    window["due_pay_results"].update(values=display, visible=True)
                    window["-DUE_HEADER-"].update(visible=True)
                else:
                    window["-DUE_WRAP-"].update(visible=False)
        elif event == "Due Payments":
            if window["-DUE_WRAP-"].visible:
                window["-DUE_WRAP-"].update(visible=False)
            else:
                due_pay_cache = check_due_payments()
                if due_pay_cache:
                    display = [[r[0], r[1] or "", r[5] or "", r[2], r[3] or "", f"\u20b1{float(r[4]):,.2f}" if r[4] else "--", "Overdue"] for r in due_pay_cache]
                    window["due_pay_results"].update(values=display, visible=True)
                    window["-DUE_HEADER-"].update(visible=True)
                    window["-DUE_WRAP-"].update(visible=True)
                else:
                    window["-DUE_WRAP-"].update(visible=False)
                    sg.popup("No due payments!")
        elif isinstance(event, tuple) and event[0] == "due_pay_results":
            if len(event) > 2 and event[2] is not None and isinstance(event[2], tuple):
                row_idx, col_idx = event[2][0], event[2][1]
                if row_idx is None or row_idx < 0:
                    pass
                elif row_idx < len(due_pay_cache):
                    sel = due_pay_cache[row_idx]
                    pending_due_ins_id = sel[0]
                    window["-PAY_FORM_WRAP-"].update(visible=True)
                    window["-PAY_HEADER-"].update(visible=True)
                    window["-PAY_FIELDS-"].update(visible=True)
                    set_pay_mode("Record Payment")
                    window["pay_property_id"].update(sel[6] or "")
                    try:
                        pay_amount_str = f"\u20b1{float(sel[4]):,.2f}" if sel[4] else "\u20b1"
                    except (ValueError, TypeError):
                        pay_amount_str = "\u20b1"
                    window["pay_amount"].update(pay_amount_str)
                    window["pay_date"].update(datetime.now().strftime("%Y-%m-%d"))
                    window["pay_status"].update("Paid")
                    window["save_pay_btn"].update("Save Payment")
        elif event == "Generate Report":
            conn = sqlite3.connect("primarius.db")
            c = conn.cursor()
            report_type = values["report_type"]
            report_title = report_type
            if report_type == "Overdue Payments":
                c.execute("""SELECT payments.date, properties.name, payments.amount
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             WHERE payments.status='Overdue'""")
                rows = c.fetchall()
                report_cache = [[r[1] or "", r[2], r[0] or "", ""] for r in rows]
            elif report_type == "Payments by Client":
                c.execute("""SELECT properties.client_name, SUM(payments.amount), MAX(payments.date), COUNT(payments.id)
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             WHERE properties.client_name IS NOT NULL
                             GROUP BY properties.client_name
                             ORDER BY SUM(payments.amount) DESC""")
                rows = c.fetchall()
                report_cache = [[r[0] or "", r[1], r[2] or "", r[3]] for r in rows]
            elif report_type == "Payments by Property":
                c.execute("""SELECT properties.location, SUM(payments.amount), MAX(payments.date), COUNT(payments.id)
                             FROM payments
                             JOIN properties ON payments.property_id = properties.id
                             GROUP BY properties.location
                             ORDER BY SUM(payments.amount) DESC""")
                rows = c.fetchall()
                report_cache = [[r[0] or "", r[1], r[2] or "", r[3]] for r in rows]
            conn.close()
            report_sort_col = None
            report_sort_asc = True
            refresh_report_table()
        elif event == "report_type":
            window["report_output"].update(visible=False)
        elif isinstance(event, tuple) and event[0] == "report_results":
            if len(event) > 2 and event[2] is not None and isinstance(event[2], tuple):
                row_idx, col_idx = event[2][0], event[2][1]
                if row_idx is None or row_idx < 0:
                    if col_idx is not None and col_idx >= 0:
                        if col_idx == report_sort_col:
                            report_sort_asc = not report_sort_asc
                        else:
                            report_sort_col = col_idx
                            report_sort_asc = True
                        refresh_report_table()
        elif event == "Export Report":
            if not report_cache:
                sg.popup("Generate a report first.")
                continue
            fname = sg.popup_get_file("Save report as...", save_as=True, default_extension=".xlsx",
                                      file_types=(("Excel Files", "*.xlsx"), ("All Files", "*.*")))
            if not fname:
                continue
            try:
                from openpyxl import Workbook
                wb = Workbook()
                ws = wb.active
                ws.title = "Report"
                ws.append([values["report_type"], f"generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
                ws.append([])
                ws.append(["Item", "Amount", "Date", "Payments"])
                for r in report_cache:
                    ws.append([r[0], r[1], r[2] or "", r[3] if r[3] else ""])
                for col, width in zip("ABCD", [30, 15, 14, 10]):
                    ws.column_dimensions[col].width = width
                for row in ws.iter_rows(min_row=3, max_row=3):
                    for cell in row:
                        cell.font = cell.font.copy(bold=True)
                wb.save(fname)
                sg.popup("Report exported successfully!")
            except Exception as e:
                sg.popup(f"Export failed: {e}")
    window.close()
    login_window()

# Initialize database and start the application
if __name__ == "__main__":
    init_db()
    login_window()
