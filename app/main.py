# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from databases import Database
from sqlalchemy import (
    Date, Text, MetaData, Table, Column, Integer, DateTime, func
)
import os
from dotenv import load_dotenv
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import uuid
import base64

app = FastAPI()
templates = Jinja2Templates(directory="templates")
load_dotenv()

COMPANY_EMAIL = os.getenv("COMPANY_EMAIL")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Initialize the database connection
database = Database(DATABASE_URL)
metadata = MetaData()

# Updated table model for Service Request Form
service_request_forms = Table(
    "service_request_forms",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("customer_name", Text),
    Column("account_number", Text),
    Column("customer_address", Text),
    Column("contact_phone", Text),
    Column("contact_email", Text),
    Column("issue_description", Text),
    Column("date", Date),
    Column("salesperson_name", Text),
    Column("requester_name", Text),
    Column("ip_address", Text),
    Column("created_at", DateTime, default=func.now()),
)

@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()

@app.on_event("shutdown")
async def shutdown():
    if database.is_connected:
        await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/confirmation", response_class=HTMLResponse)
async def confirmation_page(request: Request, customer_name: str = None):
    return templates.TemplateResponse(
        "confirmation.html",
        {"request": request, "customer_name": customer_name},
    )

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(request: Request):
    # Grab all form fields
    form_data = await request.form()
    ip_address = request.client.host

    customer_name = form_data.get("customer_name")
    account_number = form_data.get("account_number")
    customer_address = form_data.get("customer_address")
    contact_phone = form_data.get("contact_phone")
    contact_email = form_data.get("contact_email")
    issue_description = form_data.get("issue_description")
    date_str = form_data.get("date")
    salesperson_name = form_data.get("salesperson_name")
    requester_name = form_data.get("requester_name")

    # Convert date (YYYY-MM-DD) -> date object
    try:
        date_value = (
            datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        )
    except ValueError:
        date_value = None

    # Generate a unique form ID for tracking
    form_id = str(uuid.uuid4())
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Structure for PDF rendering
    full_form_data = {
        "customer_name": customer_name,
        "account_number": account_number,
        "customer_address": customer_address,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
        "issue_description": issue_description,
        "date": date_value,
        "salesperson_name": salesperson_name,
        "requester_name": requester_name,
        "ip_address": ip_address,
        "form_id": form_id,
        "current_datetime": current_datetime,
    }

    # Prepare DB insert
    query_data = {
        "customer_name": customer_name,
        "account_number": account_number,
        "customer_address": customer_address,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
        "issue_description": issue_description,
        "date": date_value,
        "salesperson_name": salesperson_name,
        "requester_name": requester_name,
        "ip_address": ip_address,
    }

    insert_query = service_request_forms.insert().values(**query_data)
    await database.execute(insert_query)

    # Generate PDF from template
    pdf_data = generate_pdf(full_form_data)

    # Email bodies
    company_body = (
        "A new Service Request Form was submitted.\n"
        "Please see the attached PDF."
    )

    customer_body = (
        "Thank you. Your service request has been received by Graves Foods.\n"
        "Please see the attached copy of your request for your records."
    )

    # Send internal copy to company
    send_email(
        COMPANY_EMAIL,
        "New Service Request Form Submission",
        company_body,
        pdf_data,
    )

    # Send confirmation copy to contact email (required field)
    if contact_email:
        send_email(
            contact_email,
            "Your Service Request Submission",
            customer_body,
            pdf_data,
        )

    # Return confirmation page
    return templates.TemplateResponse(
        "confirmation.html",
        {"request": request, "customer_name": customer_name},
    )


def generate_pdf(data: dict) -> bytes:
    """
    Generate a PDF from template using the data dictionary.
    This version is for the Service Request Form.
    """
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("pdf_template.html")

    # Convert date to string for display
    date_str = data["date"].strftime("%Y-%m-%d") if data["date"] else ""

    # Embed logo as base64 for PDF
    with open("assets/logo_sm.png", "rb") as image_file:
        logo_data = base64.b64encode(image_file.read()).decode("utf-8")

    html_content = template.render(
        customer_name=data["customer_name"],
        account_number=data["account_number"],
        customer_address=data["customer_address"],
        contact_phone=data["contact_phone"],
        contact_email=data["contact_email"],
        date=date_str,
        salesperson_name=data["salesperson_name"],
        requester_name=data["requester_name"],
        issue_description=data["issue_description"],
        ip_address=data["ip_address"],
        form_id=data["form_id"],
        current_datetime=data["current_datetime"],
        logo_data=logo_data,
    )

    pdf_data = HTML(string=html_content).write_pdf()
    return pdf_data


def send_email(to_email: str, subject: str, body: str, pdf_data: bytes):
    """
    Send an email with the Service Request Form PDF attached.
    """
    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach PDF
    pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
    pdf_attachment.add_header(
        "Content-Disposition",
        'attachment; filename="Service_Request_Form.pdf"',
    )
    msg.attach(pdf_attachment)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(FROM_EMAIL, to_email, msg.as_string())
    server.quit()
