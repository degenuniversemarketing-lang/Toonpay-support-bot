import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    SUPER_ADMIN_ID = int(os.environ['SUPER_ADMIN_ID'])
    DATABASE_URL = os.environ['DATABASE_URL']
    
    # Message templates
    WELCOME_MESSAGE = """🎫 Welcome to ToonPay Support Bot!

I'm here to help you with any issues you might have.

Please use /new to create a new support ticket."""

    SUPPORT_MESSAGE = """📬 Need help from ToonPay Support?

Click the button below to submit your ticket privately.
Our support team will assist you within 24 hours."""

    CONTACT_REQUEST = """Please provide your contact information:

1. Send your email address
2. Then send your phone number"""

    TICKET_CREATED = """✅ Your ticket has been created!

Ticket ID: #{}
We'll get back to you soon."""
