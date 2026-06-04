import requests
from django.conf import settings

class WhatsAppService:
    BASE_URL = "https://cloudapi.wafortius.com/api/v1.0/messages/send-template/15558974673"

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"
        }

    def send_template(self, number, template_name, language="en", components=None):
        if components is None:
            components = []

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": str(number),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components
            }
        }

        response = requests.post(self.BASE_URL, json=payload, headers=self.headers)

        return {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response": response.json()
        }
