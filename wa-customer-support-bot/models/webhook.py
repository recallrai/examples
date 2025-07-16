from pydantic import BaseModel
from typing import Optional, Any, Dict

class WebhookData(BaseModel):
    id: Optional[str] = None
    created: Optional[str] = None
    whatsappMessageId: Optional[str] = None
    conversationId: Optional[str] = None
    ticketId: Optional[str] = None
    text: Optional[str] = None
    type: Optional[str] = None
    data: Optional[Any] = None
    sourceId: Optional[str] = None
    sourceUrl: Optional[str] = None
    timestamp: Optional[str] = None
    owner: Optional[bool] = None
    eventType: Optional[str] = None
    statusString: Optional[str] = None
    avatarUrl: Optional[str] = None
    assignedId: Optional[str] = None
    operatorName: Optional[str] = None
    operatorEmail: Optional[str] = None
    waId: Optional[str] = None
    messageContact: Optional[Dict[str, Any]] = None
    senderName: Optional[str] = None
    listReply: Optional[Dict[str, Any]] = None
    interactiveButtonReply: Optional[Dict[str, Any]] = None
    buttonReply: Optional[Dict[str, Any]] = None
    replyContextId: Optional[str] = None
    sourceType: Optional[int] = None
    frequentlyForwarded: Optional[bool] = None
    forwarded: Optional[bool] = None

class WebhookResponse(BaseModel):
    status: str
    response: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None
