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

    def _call_back(self, tx_ref):
        if tx_ref is None:
            raise NotFound("payment reference is  required", code="payment_ref_not_found")
        base_url = getattr(settings, "BASE_URL")
        if base_url is None:
            raise NotFound("Base URl not found", code="base_url_not_found")
        return base_url + f"api/v1/jdc/payment/{tx_ref}/verify"
    
    def _get_initailizer(self):
        chapa_initializer_url = getattr(settings, "CHAPA_INIT_URL")
        if chapa_initializer_url is None:
            raise NotFound("Chapa Initializer not found", code="request_with_no_url")
        return chapa_initializer_url
    
    def _get_verify_url(self, tx_ref):
        chapa_verification_url = getattr(settings, "CHAPA_VERIFY_URL")
        if chapa_verification_url is None:
            raise NotFound("Chapa verification url not found", code="verification_url_not_found")
        return chapa_verification_url + f"/{tx_ref}/"
    
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
    
    def initialize_payment(self, email: str, amount: float, first_name: str, last_name: str, tx_ref: str):
        callback_url = self._call_back(tx_ref=tx_ref)
        payment = Payment()
        payment.email = email
        payment.first_name = first_name
        payment.last_name = last_name
        payment.amount = float(amount)
        payment.tx_ref = tx_ref
        payment.callback_url = callback_url
        payment.customization = {
            "title": "Skill Purchase",
            "description": "payment for child skill path",
        }
        payload  = payment.to_dict()
        print(f"Payment payload: {payload}")
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
    
    def verify_payment(self, tx_ref):
        if tx_ref is None:
            raise NotFound("Transaction reference is required for payment verification", code="missing_tx_ref")
        payload = dict()
        verification_url = self._get_verify_url(tx_ref)
        print(verification_url)
        headers = self._get_headers()
        try:
            response = requests.get(url=verification_url, data=payload, headers=headers)
        except requests.exceptions.RequestException as e:
            raise NotFound(f"Error verifying payment {e}", code="payment_verification_error")
        except Exception as e:
            raise NotFound(f"An unexpected error occurred during payment verification: {e}", code="unexpected_verification_error")
        return response.json()
