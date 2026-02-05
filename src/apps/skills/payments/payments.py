from django.conf import settings

from rest_framework.exceptions import NotFound

from typing import Dict
import requests

class Payment:
    def __init__(self):
        self.email: str = None
        self.first_name: str = None
        self.last_name: str = None
        self.amount: str = None
        self.tx_ref: str = None
        self.callback_url:str = None
        self.return_url: str = None
        self.currency: str = "ETB"
        self.customization: Dict[str, str] = None

    def _get_secret(self):
        chapa_secret_key = getattr(settings, "CHAPA_SECRET_KEY")
        if chapa_secret_key is None:
            raise NotFound("Chapa secret not found", code="invalid_api__secret")
        return chapa_secret_key


    def _get_initailizer(self):
        chapa_initializer_url = getattr(settings, "CHAPA_INIT_URL")
        if chapa_initializer_url is None:
            raise NotFound("Chapa Initializer not found", code="request_with_no_url")
        return chapa_initializer_url
    
    def to_dict(self):
        return {
            "email": self.email,
            "fist_name": self.first_name,
            "last_name": self.last_name,
            "amount": self.amount,
            "tx_ref": self.tx_ref,
            "currency": self.currency,
            "callback_url": self.callback_url,
            "return_url": self.return_url,
            "customization": self.customization

        }

    def _get_headers(self):
        headers = dict()
        if self._get_secret() is not None:
            headers.update({ 
                "Authorization": f"Bearer {self._get_secret()}",
                "Content-Type": "application/json"
            })
        return headers
    
    def _initialize_payment(self, email: str, amount: float, first_name: str, last_name: str, tx_ref: str):
        payment = Payment()
        payment.email = email
        payment.first_name = first_name
        payment.last_name = last_name
        payment.amount = float(amount)
        payment.tx_ref = tx_ref
        payment.customization = {
            "title": "Skill Purchase",
            "description": "payment for child skill path",
        }
        payload  = payment.to_dict()
        headers = self._get_headers()
        chapa_initializer = self._get_initailizer() 
        try:
            response = requests.post(url=chapa_initializer, json=payload, headers=headers)
            print(response.status_code)
        except requests.exceptions.RequestException as e:
            raise NotFound(f"Error initializing payment {e}", code="payment_initialization_error")
        except Exception as e:
            raise NotFound(f"An unexpected error occurred during payment initialization: {e}", code="unexpected_payment_error") 

        return response.json()