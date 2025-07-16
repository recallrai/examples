import openai
from config import get_settings
from logger import get_logger
from fastapi import FastAPI, HTTPException
from models import WebhookData, WebhookResponse, WatiSendMessageRequest, WatiApiResponse, HealthResponse
from typing import Optional
from recallrai import RecallrAI
from recallrai.models import SessionStatus
from recallrai.exceptions import UserNotFoundError
import httpx

settings = get_settings()
logger = get_logger()
app = FastAPI(title="WhatsApp Customer Support Bot with WATI Integration", version="1.0.0")

# Initialize clients
rai_client = RecallrAI(
    api_key=settings.RECALLRAI_API_KEY,
    project_id=settings.RECALLRAI_PROJECT_ID,
)
oai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def send_whatsapp_message(data: WatiSendMessageRequest) -> WatiApiResponse:
    """Send message via WATI API"""
    url = f"{settings.WATI_BASE_URL}/sendSessionMessage/{data.phone_number}"
    headers = {
        "Authorization": settings.WATI_API_TOKEN,
        "Content-Type": "application/json"
    }
    params = {
        "messageText": data.message_text,
    }
    if data.reply_context_id:
        params["replyContextId"] = data.reply_context_id
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params, headers=headers)
        logger.info(f"Response from WATI: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            return WatiApiResponse(**response.json())
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

async def process_user_message(phone_number: str, message_text: str, reply_context_id: Optional[str] = None) -> str:
    """Process incoming WhatsApp message"""
    user_id = f"whatsapp_{phone_number}_prod"
    
    # Get or create user
    try:
        user = rai_client.get_user(user_id)
    except UserNotFoundError:
        user = rai_client.create_user(user_id)
    
    # Get the most recent session and check if it's still unprocessed
    session = user.list_sessions(offset=0, limit=1).sessions
    if session == []:
        session = user.create_session(auto_process_after_minutes=5)
    else:
        session = session[0]
        if session.status == SessionStatus.PENDING:
            session = user.get_session(session.session_id)
        else:
            session = user.create_session(auto_process_after_minutes=5)
    
    # Add user message to Recallr AI
    session.add_user_message(message_text)
    
    # Get previous messages in the session (if any)
    previous_messages = []
    for message in session.get_messages():
        previous_messages.append({
            "role": message.role,
            "content": message.content,
        })
    
    # Get context from RecallrAI
    context = session.get_context()
    
    # Create system prompt with context
    system_prompt = f"""You are Zostel's Customer Support Assistant, known as a Zobu, equipped with advanced AI and full access to a comprehensive memory database for detailed historical context and customer profiles.
You have access to a long term memory system which helps you recall past interactions and customer preferences.

MEMORIES ABOUT THE USER:
{context.context}

Your primary objective is to resolve customer queries swiftly, accurately, and empathetically by following the Zobu Protocol:
    1.	Greeting and Acknowledgement:
        •	Greet customers warmly using "Zo Zo ".
        •	Recognize their past interactions and thank them for reaching out.
    2.	Probe and Understand:
        •	Ask relevant, empathetic questions to ensure full clarity of the customer's issue.
    3.	Empathy and Ownership:
        •	Express genuine empathy for issues raised and confirm that the issue is being addressed responsibly.
    4.	Action and Verification:
        •	Clearly outline the steps you'll take to resolve the issue.
        •	Verify information with relevant property teams via Slack channels as needed.
    5.	Resolution and Closure:
        •	Inform the customer promptly of the resolution.
        •	Ensure the conversation ends positively with Zobu always having the last message, using "Zo Zo Zo" or "Welcome" to conclude the interaction.
    6.	Tagging and Documentation:
        •	Use appropriate tags (#URGENT, #MODIFICATIONS, #ONGOING, #ESCALATION, #FEEDBACK, #REFUND).
        •	Document interactions meticulously, including relevant Slack message links in the NOTES section.
    7.	Communication Guidelines:
        •	Maintain professional yet engaging, friendly, and concise communication.
        •	Avoid transferring conversations unnecessarily; seek solutions proactively through existing resources.
    8.	Tools Utilization:
        •	Leverage tools provided (WATI, PMS, admin.zostel.com, Slack channels).
    9.	Collaboration:
        •	Actively participate in shift handovers, ensuring clear communication of ongoing tasks.
        •	Engage proactively during powerplay overlaps to efficiently clear backlog.
    10.	Continuous Learning:
        •	Regularly update yourself with latest protocols, policies, and case-specific learnings available in resources like Ezee tutorials and internal documentation.

Ensure all interactions reflect Zostel's vibrant, community-driven ethos, and strive for excellence in customer satisfaction.
Only give short and concise responses, avoiding unnecessary details."""
    
    # Get LLM response
    response = await oai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    assistant_message = response.choices[0].message.content
    
    # Add assistant response to RecallrAI
    session.add_assistant_message(assistant_message)
    
    # Send response via WhatsApp
    logger.info(f"Assistant [{phone_number}]: {assistant_message}")
    await send_whatsapp_message(WatiSendMessageRequest(
        phone_number=phone_number,
        message_text=assistant_message,
        reply_context_id=reply_context_id
    ))
    
    return assistant_message

@app.post("/webhook", response_model=WebhookResponse)
async def wati_webhook(data: WebhookData) -> WebhookResponse:
    """Webhook to receive WATI messages"""
    try:
        # Check if it's an incoming message (not from us)
        if data.eventType == 'message' and data.owner == False:
            phone_number = data.waId
            # Ignore messages from phone numbers not in the allowed list
            if phone_number not in settings.ALLOWED_PHONE_NUMBERS:
                logger.info(f"Ignoring message from phone number: {phone_number}")
                return WebhookResponse(status="ignored", reason="phone number not allowed")
            
            logger.info(f"Received webhook data: {data.model_dump_json()}")

            # Extract message text based on message type
            message_text = None
            message_type = data.type
            
            if message_type == 'text':
                message_text = data.text
            elif message_type == 'button' and data.buttonReply:
                message_text = data.buttonReply.get('text')
            elif message_type == 'list' and data.listReply:
                message_text = data.listReply.get('title')
            
            if phone_number and message_text:
                # Process the message
                response = await process_user_message(phone_number, message_text, data.whatsappMessageId)
                return WebhookResponse(status="success", reason=f"Assistant [{phone_number}]: {response}")
            else:
                logger.warning(f"Missing phone_number ({phone_number}) or message_text ({message_text})")
                return WebhookResponse(status="ignored", reason="missing required fields")
        
        return WebhookResponse(status="ignored", reason="not an incoming message")
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return WebhookResponse(status="error", reason=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")
