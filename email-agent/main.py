from openai import OpenAI
from config import get_settings
from recallrai import RecallrAI
from recallrai.exceptions import UserNotFoundError

settings = get_settings()

# Setup Clients
oai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
)
rai_client = RecallrAI(
    api_key=settings.RECALLRAI_API_KEY,
    project_id=settings.RECALLRAI_PROJECT_ID,
)

# Get user
try:
    user = rai_client.get_user(user_id=settings.RECALLRAI_USER_ID)
except UserNotFoundError as e:
    user = rai_client.create_user(
        user_id=settings.RECALLRAI_USER_ID,
        metadata={},
    )
