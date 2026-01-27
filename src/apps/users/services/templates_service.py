from datetime import datetime

def genrate_context_for_otp(code, verification_url, user):
    subject = "Your One Time Password (OTP) Code"
    return {
        "code": code,
        "user": user,
        "template_name": "users/otp_template.html",
        "subject": subject,
        "verification_url": verification_url,
        "year": datetime.now().year
    }