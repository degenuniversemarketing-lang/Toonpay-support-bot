import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    # Remove any spaces, dashes, or parentheses
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's a valid phone number (simple validation)
    pattern = r'^\+?[\d]{10,15}$'
    return re.match(pattern, phone) is not None

def sanitize_input(text):
    # Remove any potentially harmful characters
    return re.sub(r'[<>]', '', text)
