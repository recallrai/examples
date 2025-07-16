from pydantic import BaseModel
from typing import Optional, Any, Dict

class WatiMessage(BaseModel):
    whatsappMessageId: str
    localMessageId: str
    text: Optional[str] = None
    media: Optional[Any] = None
    messageContact: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    type: str
    time: str
    status: int
    statusString: str
    isOwner: bool
    botType: Optional[str] = None
    isUnread: bool
    ticketId: str
    avatarUrl: Optional[str] = None
    assignedId: Optional[str] = None
    operatorName: Optional[str] = None
    replyContextId: Optional[str] = None
    sourceType: int
    failedDetail: Optional[str] = None
    messageReferral: Optional[Dict[str, Any]] = None
    googleAdsReferral: Optional[Dict[str, Any]] = None
    messageProducts: Optional[Any] = None
    orderProducts: Optional[Any] = None
    orderDetails: Optional[Any] = None
    paymentStatus: Optional[str] = None
    interactiveData: Optional[Dict[str, Any]] = None
    referenceOrderId: Optional[str] = None
    isDeleted: bool
    replyButtonPayload: Optional[str] = None
    reactions: Optional[Any] = None
    audioTranscriptionStatus: Optional[str] = None
    filePath: Optional[str] = None
    isDelayed: bool
    id: str
    tenantId: str
    created: str
    conversationId: str
    channelId: Optional[str] = None
    channelType: int

class WatiApiResponse(BaseModel):
    ok: bool
    result: str
    message: WatiMessage

class WatiSendMessageRequest(BaseModel):
    phone_number: str
    message_text: str
    reply_context_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
