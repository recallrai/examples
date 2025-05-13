from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from .models import SendEmailRequest
from config import get_settings

settings = get_settings()

credential = AzureKeyCredential(settings.ACS_KEY)
acs_client = EmailClient(
    endpoint=settings.ACS_ENDPOINT,
    credential=credential
)

def send_email(data: SendEmailRequest) -> bool:
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
    
    poller = acs_client.begin_send(message)
    result = poller.result()
    
    return result["status"] == "Succeeded"
