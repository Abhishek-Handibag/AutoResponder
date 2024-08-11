import smtplib
import imaplib
import email
import time
import csv
import os
from email.mime.text import MIMEText
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv('EMAIL_ADDRESS')
PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = 'smtp.gmail.com'
IMAP_SERVER = 'imap.gmail.com'

TRIGGER_WORDS = [
    'help', 'support', 'issue', 'ticket', 'query', 'problem', 
    'question', 'error', 'assistance', 'trouble', 'bug', 
    'complaint', 'request', 'difficulty', 'fault', 'glitch', 
    'malfunction', 'concern', 'inquiry', 'urgent', 'emergency',
    'service', 'downtime', 'failure', 'unable', 'crash', 'delay',
    'pending', 'lost', 'refund', 'cancel', 'payment', 'billing'
]

CSV_FILE = 'processed_emails.csv'

def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

def check_inbox(mail):
    mail.select('inbox')
    result, data = mail.search(None, 'ALL')
    return data[0].split()

def generate_ticket_id():
    return str(uuid4())

def send_response(recipient, ticket_id):
    # HTML content for the email
    html_content = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px;">
                <h2 style="text-align: center; color: #333;">Thank You for Being a Valued Customer!</h2>
            </div>
            <div style="margin-top: 20px;">
                <p>Dear Customer,</p>
                <p>Thank you for reaching out to us. We appreciate your patience and understanding as we work to assist you with your issue.</p>
                <p>Your ticket ID is <strong>{ticket_id}</strong>. Our team will review your request and get back to you shortly.</p>
                <p>If you have any further questions or need additional support, please feel free to reply to this email.</p>
                <p>Best regards,</p>
                <p>Your Support Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEText(html_content, 'html')
    msg['Subject'] = 'Ticket Confirmation'
    msg['From'] = EMAIL
    msg['To'] = recipient

    with smtplib.SMTP_SSL(SMTP_SERVER) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, recipient, msg.as_string())

def extract_body(msg):
    """Extracts email body from a message object, handles multipart emails."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
    return ''

def load_processed_emails():
    """Loads processed emails from the CSV file."""
    if not os.path.exists(CSV_FILE):
        return set()
    
    with open(CSV_FILE, mode='r') as file:
        reader = csv.reader(file)
        return set(row[0] for row in reader)

def save_processed_email(email_address):
    """Saves a processed email to the CSV file."""
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([email_address])

def process_emails(mail, processed_emails):
    for num in check_inbox(mail):
        result, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        sender = msg['From']
        
        if sender in processed_emails:
            continue  # Skip this email if it's already been processed

        body = extract_body(msg)

        # Check if any of the specific words are in the email body
        if any(word in body.lower() for word in TRIGGER_WORDS):
            ticket_id = generate_ticket_id()
            send_response(sender, ticket_id)
            print(f"Sent response to {sender} with ticket ID {ticket_id}")
            save_processed_email(sender)
            processed_emails.add(sender)  # Add to the set to prevent duplicates

if __name__ == "__main__":
    try:
        processed_emails = load_processed_emails()
        while True:
            mail = connect_to_email()
            print("Connected to email successfully.")
            process_emails(mail, processed_emails)
            time.sleep(60)
    except Exception as e:
        print(f"An error occurred: {e}")
