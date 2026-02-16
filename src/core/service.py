from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import HttpRequest
from rest_framework.response import Response
from rest_framework  import permissions
from rest_framework.exceptions import ValidationError

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from django.conf import settings
import os


@api_view(http_method_names=["get"])
@permission_classes(permission_classes=[permissions.IsAuthenticated])
def health_check(request: HttpRequest) -> Response:
    """ A simple api view for project health check """
    return Response(data={"status": "succes", "detail": {"users": "/api/v1/auth/","skills": "/api/v1/skills/", "lessons": "/api/v1/lessons/"}})

@permission_classes(permission_classes=[permissions.IsAuthenticated])
@api_view(http_method_names=["get"])
def test_send_email(request: HttpRequest) -> Response:
    """ Test email notification using sendgrid """
    try:
        email_client = SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"), host="https://api.sendgrid.com")
        message = Mail(from_email=Email(email="ogennaisrael98@gmail.com"), to_emails=To(email="ogennaisrael@gmail.com"), subject="Sending email with twilio sendgrid.", 
                   html_content=Content("text/plain", "<strong>and easy to do anywhere, even with Python</strong>"))
    
        print(email_client)
        response = email_client.send(message)
        print(response.status_code)
        print(response.body)
        return Response("ok")
    except Exception as e: 
        raise 
