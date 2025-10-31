# main.py

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from databases import Database
from sqlalchemy import (
    Date, Text, Time, MetaData, Table, Column, Integer, Boolean, DateTime, func
)
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
load_dotenv()

COMPANY_EMAIL = os.getenv("COMPANY_EMAIL")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")
DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)

metadata = MetaData()

service_forms = Table(
    "service_forms",
    metadata,
    Column('id', Integer, primary_key=True),
    Column('technician_name', Text),
    Column('customer_name', Text),
    Column('customer_email', Text),
    Column('date', Date),
    Column('time', Time),
    Column('ip_address', Text),
    Column('machine_name', Text),
    Column('model', Text),
    Column('dispenser', Text),
    Column('distribution', Text),
    Column('titration', Text),
    Column('wash_temp', Text),
    Column('rinse_tank_temp', Text),
    Column('final_rinse_psi', Text),
    Column('water_hardness', Text),
    Column('products', Text),
    Column('stock_check', Text),
    Column('comments', Text),
    Column('service_rep_signature', Text),
    Column('customer_signature', Text),
    Column('fill_valves', Boolean),
    Column('pumps', Boolean),
    Column('wash_tank_arms', Boolean),
    Column('rinse_tank_arms', Boolean),
    Column('final_rinse', Boolean),
    Column('overflow', Boolean),
    Column('drains', Boolean),
    Column('racking', Boolean),
    Column('curtains', Boolean),
    Column('odor', Boolean),
    Column('feel', Boolean),
    Column('stain_removal', Boolean),
    Column('water_levels', Boolean),
    Column('wettability_poor', Boolean),
    Column('wettability_good', Boolean),
    Column('drain_valves', Boolean),
    Column('second_look', Boolean),
    Column('coffee', Boolean),
    Column('tea', Boolean),
    Column('hot_chocolate', Boolean),
    Column('juice', Boolean),
    Column('warmer_element', Boolean),
    Column('switches_lights', Boolean),
    Column('sprayhead_tubing', Boolean),
    Column('brewbasket', Boolean),
    Column('timer_valve', Boolean),
    Column('relay_wiring', Boolean),
    Column('thermostat', Boolean),
    Column('micromet_feeder', Boolean),
    Column('water_level', Boolean),
    Column('timed_cycle', Boolean),
    Column('temperature', Boolean),
    Column('um_bypass', Boolean),
    Column('um_glass', Boolean),
    Column('um_pump', Boolean),
    Column('um_agitator', Boolean),
    Column('water_valve', Boolean),
    Column('drip_tray', Boolean),
    Column('switch', Boolean),
    Column('tea_head', Boolean),
    Column('motor', Boolean),
    Column('valve', Boolean),
    Column('timer', Boolean),
    Column('hopper_auger', Boolean),
    Column('other', Boolean),
    Column('created_at', DateTime, default=func.now())
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/confirmation", response_class=HTMLResponse)
async def confirmation_page(request: Request, customer_name: str = None):
    return templates.TemplateResponse("confirmation.html", {"request": request, "customer_name": customer_name})

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    technician_name: str = Form(...),
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    date: str = Form(...), 
    time: str = Form(None),  
    machine_name: str = Form(None),
    model: str = Form(None),
    dispenser: str = Form(None),
    distribution: str = Form(None),
    titration: str = Form(None),
    wash_temp: str = Form(None),
    rinse_tank_temp: str = Form(None),
    final_rinse_psi: str = Form(None),
    water_hardness: str = Form(None),
    products: str = Form(None),
    stock_check: str = Form(None),
    comments: str = Form(None),
    service_rep_signature: str = Form(...),
    customer_signature: str = Form(...),
    fill_valves: bool = Form(False),
    pumps: bool = Form(False),
    wash_tank_arms: bool = Form(False),
    rinse_tank_arms: bool = Form(False),
    final_rinse: bool = Form(False),
    overflow: bool = Form(False),
    drains: bool = Form(False),
    racking: bool = Form(False),
    curtains: bool = Form(False),
    odor: bool = Form(False),
    feel: bool = Form(False),
    stain_removal: bool = Form(False),
    water_levels: bool = Form(False),
    wettability_poor: bool = Form(False),
    wettability_good: bool = Form(False),
    drain_valves: bool = Form(False),
    second_look: bool = Form(False),
    coffee: bool = Form(False),
    tea: bool = Form(False),
    hot_chocolate: bool = Form(False),
    juice: bool = Form(False),
    warmer_element: bool = Form(False),
    switches_lights: bool = Form(False),
    sprayhead_tubing: bool = Form(False),
    brewbasket: bool = Form(False),
    timer_valve: bool = Form(False),
    relay_wiring: bool = Form(False),
    thermostat: bool = Form(False),
    micromet_feeder: bool = Form(False),
    water_level: bool = Form(False),
    timed_cycle: bool = Form(False),
    temperature: bool = Form(False),
    um_bypass: bool = Form(False),
    um_glass: bool = Form(False),
    um_pump: bool = Form(False),
    um_agitator: bool = Form(False),
    water_valve: bool = Form(False),
    drip_tray: bool = Form(False),
    switch: bool = Form(False),
    tea_head: bool = Form(False),
    motor: bool = Form(False),
    valve: bool = Form(False),
    timer: bool = Form(False),
    hopper_auger: bool = Form(False),
    other: bool = Form(False)
):
    
    ip_address = request.client.host

    # Parse the date string into a datetime.date object
    try:
        date_value = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        date_value = None  # Handle error as needed

    # Parse the time string into a datetime.time object
    if time:
        try:
            time_value = datetime.strptime(time, "%H:%M").time()
        except ValueError:
            time_value = None  # Handle error as needed
    else:
        time_value = None

    # Collect all form data into a dictionary for generating the PDF
    form_data = {
        "technician_name": technician_name,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "date": date_value,
        "time": time_value,
        "ip_address": ip_address,
        "machine_name": machine_name,
        "model": model,
        "dispenser": dispenser,
        "distribution": distribution,
        "titration": titration,
        "wash_temp": wash_temp,
        "rinse_tank_temp": rinse_tank_temp,
        "final_rinse_psi": final_rinse_psi,
        "water_hardness": water_hardness,
        "products": products,
        "stock_check": stock_check,
        "comments": comments,
        "service_rep_signature": service_rep_signature,
        "customer_signature": customer_signature,
        "checkboxes": {
            "fill_valves": fill_valves,
            "pumps": pumps,
            "wash_tank_arms": wash_tank_arms,
            "rinse_tank_arms": rinse_tank_arms,
            "final_rinse": final_rinse,
            "overflow": overflow,
            "drains": drains,
            "racking": racking,
            "curtains": curtains,
            "odor": odor,
            "feel": feel,
            "stain_removal": stain_removal,
            "water_levels": water_levels,
            "wettability_poor": wettability_poor,
            "wettability_good": wettability_good,
            "drain_valves": drain_valves,
            "second_look": second_look,
            "coffee": coffee,
            "tea": tea,
            "hot_chocolate": hot_chocolate,
            "juice": juice,
            "warmer_element": warmer_element,
            "switches_lights": switches_lights,
            "sprayhead_tubing": sprayhead_tubing,
            "brewbasket": brewbasket,
            "timer_valve": timer_valve,
            "relay_wiring": relay_wiring,
            "thermostat": thermostat,
            "micromet_feeder": micromet_feeder,
            "water_level": water_level,
            "timed_cycle": timed_cycle,
            "temperature": temperature,
            "um_bypass": um_bypass,
            "um_glass": um_glass,
            "um_pump": um_pump,
            "um_agitator": um_agitator,
            "water_valve": water_valve,
            "drip_tray": drip_tray,
            "switch": switch,
            "tea_head": tea_head,
            "motor": motor,
            "valve": valve,
            "timer": timer,
            "hopper_auger": hopper_auger,
            "other": other
        }
    }

    # Prepare data for database insertion
    db_data = {
        "technician_name": technician_name,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "date": date_value,
        "time": time_value,
        "ip_address": ip_address,
        "machine_name": machine_name,
        "model": model,
        "dispenser": dispenser,
        "distribution": distribution,
        "titration": titration,
        "wash_temp": wash_temp,
        "rinse_tank_temp": rinse_tank_temp,
        "final_rinse_psi": final_rinse_psi,
        "water_hardness": water_hardness,
        "products": products,
        "stock_check": stock_check,
        "comments": comments,
        "service_rep_signature": service_rep_signature,
        "customer_signature": customer_signature,
        "fill_valves": fill_valves,
        "pumps": pumps,
        "wash_tank_arms": wash_tank_arms,
        "rinse_tank_arms": rinse_tank_arms,
        "final_rinse": final_rinse,
        "overflow": overflow,
        "drains": drains,
        "racking": racking,
        "curtains": curtains,
        "odor": odor,
        "feel": feel,
        "stain_removal": stain_removal,
        "water_levels": water_levels,
        "wettability_poor": wettability_poor,
        "wettability_good": wettability_good,
        "drain_valves": drain_valves,
        "second_look": second_look,
        "coffee": coffee,
        "tea": tea,
        "hot_chocolate": hot_chocolate,
        "juice": juice,
        "warmer_element": warmer_element,
        "switches_lights": switches_lights,
        "sprayhead_tubing": sprayhead_tubing,
        "brewbasket": brewbasket,
        "timer_valve": timer_valve,
        "relay_wiring": relay_wiring,
        "thermostat": thermostat,
        "micromet_feeder": micromet_feeder,
        "water_level": water_level,
        "timed_cycle": timed_cycle,
        "temperature": temperature,
        "um_bypass": um_bypass,
        "um_glass": um_glass,
        "um_pump": um_pump,
        "um_agitator": um_agitator,
        "water_valve": water_valve,
        "drip_tray": drip_tray,
        "switch": switch,
        "tea_head": tea_head,
        "motor": motor,
        "valve": valve,
        "timer": timer,
        "hopper_auger": hopper_auger,
        "other": other,
    }

    # Prepare data for database insertion
    db_data = form_data.copy()
    db_data.update(form_data["checkboxes"])
    del db_data["checkboxes"]

    # Insert data into the database
    query = service_forms.insert().values(**db_data)
    await database.execute(query)

    # Generate PDF with form data, including signature names
    pdf_data = generate_pdf(**form_data)

    # Email the PDF
    customer_body = (
        "The service is complete. Please find the details in the attached PDF file. "
        "Please reach out to your Graves Foods service technician if you have any questions or concerns "
        "about your service. Thank you for being a valued Graves Foods customer!"
    )
    company_body = (
        "The service is complete. Please find the details in the attached PDF file. "
        "The customer has been sent a copy of the PDF as well."
    )
    send_email(customer_email, "Service Form Submission", customer_body, pdf_data)
    send_email(COMPANY_EMAIL, "Service Form Submission", company_body, pdf_data)

    # Render confirmation page
    return templates.TemplateResponse("confirmation.html", {"request": request, "customer_name": customer_name})

def generate_pdf(
    technician_name, customer_name, customer_email, date, time, ip_address,
    machine_name, model, dispenser, distribution,
    titration, wash_temp, rinse_tank_temp, final_rinse_psi, water_hardness,
    products, stock_check, comments, checkboxes, service_rep_signature, customer_signature
):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # Add header and logo
    y = 750
    logo_path = "/root/ServiceForm/app/assets/GF_FullLogo_Primary.png"
    if os.path.exists(logo_path):
        pdf.drawImage(logo_path, 72, y, width=100, height=50)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(200, y + 30, "Graves Foods")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(200, y + 15, "913 Big Horn Drive, Jefferson City, MO, 65109")
    pdf.drawString(200, y, "Phone: (573) 893-3000 | gravesfoods.com")
    pdf.drawString(200, y - 15, "Excellence Since 1947")
    y -= 80
    
    # Set uniform font for the document
    pdf.setFont("Helvetica", 10)
    
    # Helper function for page breaks
    def check_page_space(pdf, y, spacing=20):
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            return 750
        return y - spacing
    
    # Print Basic Information
    pdf.drawString(72, y, "Basic Information")
    y = check_page_space(pdf, y, 30)
    basic_info = [
        f"Technician Name: {technician_name}",
        f"Customer Name: {customer_name}",
        f"Customer Email: {customer_email}",
        f"Date: {date.strftime('%Y-%m-%d') if date else 'N/A'}",
        f"Time: {time.strftime('%H:%M') if time else 'N/A'}",
        f"IP Address: {ip_address}",
        f"Machine Name: {machine_name or 'N/A'}",
        f"Model: {model or 'N/A'}",
        f"Dispenser: {dispenser or 'N/A'}",
        f"Distribution: {distribution or 'N/A'}",
    ]
    for line in basic_info:
        pdf.drawString(72, y, line)
        y = check_page_space(pdf, y)
    
    # Print Ware Wash Laundry Results
    pdf.drawString(72, y, "Ware Wash Laundry Results")
    y = check_page_space(pdf, y, 20)
    laundry_info = [
        f"Titration: {titration or 'N/A'}",
        f"Wash Temp: {wash_temp or 'N/A'}",
        f"Rinse Tank Temp: {rinse_tank_temp or 'N/A'}",
        f"Final Rinse P.S.I.: {final_rinse_psi or 'N/A'}",
        f"Water Hardness: {water_hardness or 'N/A'}",
    ]
    for line in laundry_info:
        pdf.drawString(72, y, line)
        y = check_page_space(pdf, y)
    
    # Checkbox Results
    pdf.drawString(72, y, "Service Checklist:")
    y = check_page_space(pdf, y, 20)
    for label, checked in checkboxes.items():
        status = "Yes" if checked else "No"
        pdf.drawString(72, y, f"{label.replace('_', ' ').title()}: {status}")
        y = check_page_space(pdf, y)
    
    # Additional Information
    pdf.drawString(72, y, "Additional Information:")
    y = check_page_space(pdf, y, 20)
    additional_info = [
        f"Products: {products or 'N/A'}",
        f"Stock Check: {stock_check or 'N/A'}",
        f"Comments: {comments or 'N/A'}",
    ]
    for line in additional_info:
        pdf.drawString(72, y, line)
        y = check_page_space(pdf, y)
    
    # Signatures
    pdf.drawString(72, y, "Signatures")
    y = check_page_space(pdf, y, 30)

    pdf.drawString(72, y, "Service Representative Signature:")
    y = check_page_space(pdf, y)
    pdf.drawString(72, y, f"{service_rep_signature or 'Not Provided'}")
    y = check_page_space(pdf, y, 30)

    pdf.drawString(72, y, "Customer Signature:")
    y = check_page_space(pdf, y)
    pdf.drawString(72, y, f"{customer_signature or 'Not Provided'}")
    y = check_page_space(pdf, y, 30)

    pdf.drawString(72, y, f"Technician Name: {technician_name}")
    y = check_page_space(pdf, y)
    pdf.drawString(72, y, f"Customer Name: {customer_name}")
    y = check_page_space(pdf, y)
    pdf.drawString(72, y, f"Date: {date.strftime('%Y-%m-%d') if date else 'N/A'}")
    y = check_page_space(pdf, y)
    pdf.drawString(72, y, f"Time: {time.strftime('%H:%M') if time else 'N/A'}")
    y = check_page_space(pdf, y)
    pdf.drawString(72, y, f"IP Address: {ip_address}")
    y = check_page_space(pdf, y)

    pdf.save()
    buffer.seek(0)
    return buffer.read()

def send_email(to_email, subject, body, pdf_data):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
    pdf_attachment.add_header('Content-Disposition', 'attachment', filename='Service_Form_Details.pdf')
    msg.attach(pdf_attachment)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(FROM_EMAIL, to_email, msg.as_string())
    server.quit()