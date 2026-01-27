from datetime import datetime

def genrate_context_for_otp(code, verification_url, email):
    subject = "Your One Time Password (OTP) Code"
    return {
        "code": code,
        "email": email,
        "template_name": "users/otp_template.html",
        "subject": subject,
        "verification_url": verification_url,
        "year": datetime.now().year
    }