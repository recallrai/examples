import streamlit as st
from openai import OpenAI
from config import get_settings
from recallrai import RecallrAI
from recallrai.exceptions import UserNotFoundError
from recallrai.models import SessionStatus
from datetime import datetime, timezone
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

# Streamlit UI setup
st.set_page_config(page_title="RecallrAI Example - Email Agent", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

# Main app layout
col1, col2 = st.columns([1, 3])

# Display current UTC time in the top right
current_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
st.markdown(f"<div style='position: absolute; top: 10px; right: 10px;'>{current_utc}</div>", unsafe_allow_html=True)

# Left sidebar with sessions list
with col1:
    st.header("Your Sessions")
    
    # Button to create a new session
    if st.button("New Session"):
        # Create a session for the user
        new_session = user.create_session(auto_process_after_minutes=5)
        st.session_state.current_session_id = new_session.session_id
        st.session_state.messages = []  # Clear messages for new session
        st.rerun()
    
    # Refresh sessions button
    if st.button("Refresh Sessions"):
        st.rerun()
    
    # List all available user sessions
    st.subheader("Previous Sessions")
    session_list = user.list_sessions(offset=0, limit=10)
    
    for session in session_list.sessions:
        # Get session status
        status = session.status
        
        created_at_str = session.created_at.strftime("%dth %B %Y %H:%M:%S %Z")
                
        # Display session with appropriate color based on status
        if status == SessionStatus.PROCESSED:
            st.success(f"Session: {session.session_id}\n\nCreated: {created_at_str}\n\nStatus: {status}")
        elif status == SessionStatus.PROCESSING:
            st.warning(f"Session: {session.session_id}\n\nCreated: {created_at_str}\n\nStatus: {status}")
        else:  # PENDING
            st.error(f"Session: {session.session_id}\n\nCreated: {created_at_str}\n\nStatus: {status}")
            
            # Add Process Session button for pending sessions
            if st.button(f"Process Session", key=f"process_{session.session_id}"):
                try:
                    session_obj = user.get_session(session_id=session.session_id)
                    session_obj.process()
                    st.success(f"Processing initiated for session {session.session_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing session: {str(e)}")
        
        # Display a separator between sessions
        st.divider()
    else:
        # If no sessions are available, show a message
        st.info("No sessions found. Create a new session to get started.")

# Right side with chat interface
with col2:
    st.header("Chat Interface")
    
    if st.session_state.current_session_id:
        st.subheader(f"Active Session: {st.session_state.current_session_id}")
    else:
        st.info("Create a new session from the sidebar to start chatting")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if st.session_state.current_session_id:
        prompt = st.chat_input("Type your message here...")
        
        if prompt:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Add message to RecallrAI session
            try:
                session = user.get_session(session_id=st.session_state.current_session_id)
                session.add_user_message(prompt)
            except Exception as e:
                st.error(f"Error adding message to RecallrAI: {str(e)}")
            
            # Display assistant response with streaming
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Get context from RecallrAI
                try:
                    context = session.get_context()
                    
                    # Create a system prompt with context
                    system_prompt = f"""You are a helpful assistant with memory of previous conversations.
                    
                    MEMORIES ABOUT THE USER:
                    {context.context}
                    
                    You can use the above memories to provide better responses to the user.
                    Don't mention that you have access to memories unless you are explicitly asked."""
                    
                    # Get response from OpenAI with streaming
                    stream = oai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                        ],
                        stream=True,
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    
                    # Save the assistant's response to session state
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    # Add assistant response to RecallrAI session
                    session.add_assistant_message(full_response)
                
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    message_placeholder.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
