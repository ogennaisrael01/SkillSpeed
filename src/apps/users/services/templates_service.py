from datetime import datetime
from typing import Dict


def genrate_context_for_otp(code=None,
                            verification_url=None,
                            email=None) -> Dict[str, str]:
    subject = "Your One Time Password (OTP) Code"
    return {
        "code": code,
        "email": email,
        "template_name": "users/otp_template.html",
        "subject": subject,
        "verification_url": verification_url,
        "year": str(datetime.now().year)
    }


def generate_context_for_password_reset(code=None,
                                        verification_url=None,
                                        email=None,
                                        name=None) -> Dict[str, str]:
    subject = "Password Reset Request (Time Limited)"
    template_name = "users/password_template.html"
    return {
        "code": code,
        "email": email,
        "verification_url": verification_url,
        "template_name": template_name,
        "name": name,
        'subject': subject,
        "year": str(datetime.now().year)
    }
