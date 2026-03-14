import os
from dotenv import load_dotenv
import logging

load_dotenv()

class Config:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    SUPER_ADMIN_ID = int(os.environ['SUPER_ADMIN_ID'])
    ADMIN_GROUP_ID = int(os.environ['ADMIN_GROUP_ID'])  # Single admin group
    DATABASE_URL = os.environ['DATABASE_URL']
    
    # Message templates
    WELCOME_MESSAGE = """🎫 **Welcome to ToonPay Support Bot!**

I'm here to help you with any issues you might have.

**How to create a ticket:**
1️⃣ Click 'New Ticket'
2️⃣ Select your issue category
3️⃣ Provide your details
4️⃣ Describe your issue
5️⃣ Submit

⏱️ **ToonPay Support Available 24/7**

Click the button below to start!"""

    SUPPORT_MESSAGE = """📬 **Need help from ToonPay Support?**

Click the button below to submit your ticket privately.
Our support team will assist you within 24 hours."""
