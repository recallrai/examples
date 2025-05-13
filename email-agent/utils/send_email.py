from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from .models import SendEmailRequest
from config import get_settings

settings = get_settings()

def send_email(self, data: SendEmailRequest) -> bool:
    message = {
        "senderAddress": settings.ACS_EMAIL,
        "recipients": {
            "to": [{"address": data.email}]
        },
        "content": {
            "subject": data.subject,
            "plainText": data.body,
        }
    }
    
    poller = self.client.begin_send(message)
    result = poller.result()
    
    return result["status"] == "Succeeded"
