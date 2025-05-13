from pydantic import BaseModel

class SendEmailRequest(BaseModel):
    email: str
    subject: str
    body: str
