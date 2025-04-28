import smtplib
from email.message import EmailMessage
import sqlite3
import datetime

# Configuration
EMAIL_CONFIG = {
    "sender": "ENTER_YOUR_EMAIl_ID",
    "password": "ENTER_YOUR_PASSWD",
    "server": "smtp.gmail.com",
    "port": 465
}

TEMPLATES = {
    "enrollment": {
        "subject": "Welcome to the Face Recognition System!",
        "body": lambda name, regno: (
            f"Hello {name},\n\nYou've been successfully enrolled.\n"
            f"Your Registration Number: {regno}\n\nBest Regards,\nAdmin Team"
        )
    },
    "attendance": {
        "subject": "Attendance Marked",
        "body": lambda name, status, remarks, date: (
            f"Hello {name},\n\nAttendance marked as '{status}'.\n"
            f"Remarks: {remarks}\nDate: {date}\n\nBest Regards,\nAdmin Team"
        )
    }
}

def send_email(to_email, subject, body):
    """Generic email sending function"""
    msg = EmailMessage()
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG["server"], EMAIL_CONFIG["port"]) as server:
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def _update_email_status(regno, date, flag_type):
    """Update email status flags in database"""
    with sqlite3.connect("identifier.sqlite") as conn:
        cursor = conn.cursor()
        query = f"UPDATE Attendance SET {flag_type} = 1 WHERE regno = ? AND date = ?"
        cursor.execute(query, (regno, date))
        conn.commit()

def send_enrollment_email(name, email, regno):
    """Send enrollment confirmation email"""
    send_email(
        email,
        TEMPLATES["enrollment"]["subject"],
        TEMPLATES["enrollment"]["body"](name, regno)
    )

def send_attendance_email(name, email, regno, status, remarks):
    """Handle attendance-related emails with status tracking"""
    current_date = datetime.datetime.now().date().isoformat()
    email_type = "exit_email" if status == "Checked Out" else "email"
    flag_column = f"{email_type}_sent"

    with sqlite3.connect("identifier.sqlite") as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {flag_column} FROM Attendance WHERE regno = ? AND date = ?",
            (regno, current_date)
        )
        record = cursor.fetchone()

        if record and record[0] == 1:
            print(f"{email_type.capitalize()} already sent for {name}")
            return True

    success = send_email(
        email,
        TEMPLATES["attendance"]["subject"],
        TEMPLATES["attendance"]["body"](name, status, remarks, current_date)
    )

    if success:
        _update_email_status(regno, current_date, flag_column)
        return True
    return False
