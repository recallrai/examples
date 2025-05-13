import streamlit as st
from openai import OpenAI
from config import get_settings
from recallrai import RecallrAI
from recallrai.exceptions import UserNotFoundError, InvalidSessionStateError
from recallrai.models import SessionStatus
from datetime import datetime, timezone
import json
from utils.tools import send_email
from utils.models import SendEmailRequest

settings = get_settings()

# Setup Clients
oai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
)
rai_client = RecallrAI(
    api_key=settings.RECALLRAI_API_KEY,
    project_id=settings.RECALLRAI_PROJECT_ID,
)

# Define the email tool for function calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to a recipient",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "The body content of the email"
                    }
                },
                "required": ["email", "subject", "body"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

# Get user
try:
    user = rai_client.get_user(user_id=settings.RECALLRAI_USER_ID)
except UserNotFoundError as e:
    user = rai_client.create_user(
        user_id=settings.RECALLRAI_USER_ID,
        metadata={},
    )
except Exception as e:
    st.error(f"Error creating user: {str(e)}")
    st.stop()

# Streamlit UI setup
st.set_page_config(page_title="RecallrAI Example - Email Agent", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

# Main app layout
col1, col2 = st.columns([1, 3])

# Left sidebar with sessions list
with col1:
    # Display current UTC time in the top right
    current_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f"<div style='position: absolute; top: 10px; right: 10px;'>{current_utc}</div>", unsafe_allow_html=True)

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
        session = user.get_session(session_id=st.session_state.current_session_id)
        if session.status != SessionStatus.PENDING:
            st.session_state.current_session_id = None
            st.session_state.messages = []
    
    # List all available user sessions
    st.subheader("Previous Sessions")
    session_list = user.list_sessions(offset=0, limit=10)
    
    if not session_list.sessions:
        # If no sessions are available, show a message
        st.info("No sessions found. Create a new session to get started.")
    
    with st.container(border=True, height=700):
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
            
            # Display function call information if present
            if message.get("function_call"):
                with st.expander("Function Call Details"):
                    st.json(message["function_call"])
            
            # Display function result if present
            if message.get("function_result"):
                with st.expander("Function Result"):
                    st.write(message["function_result"])
    
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
            except InvalidSessionStateError as e:
                st.error(f"The session you're trying to send a message to is expired. Please create a new session.")
            except Exception as e:
                st.error(f"Unknown Recallr AI Error: {str(e)}")
                st.stop()
            
            # Display assistant response with streaming
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                # Get context from RecallrAI
                try:
                    context = session.get_context()
                    print(context)
                    
                    # Create a system prompt with context
                    system_prompt = f"""You are a helpful assistant with memory of previous conversations.
                    
                    MEMORIES ABOUT THE USER:
                    {context.context}
                    
                    You can use the above memories to provide better responses to the user.
                    Don't mention that you have access to memories unless you are explicitly asked.
                    
                    You also have the ability to send emails. Use the send_email function when the user requests to send an email.
                    """
                    
                    # Get response from OpenAI with streaming and function calling
                    messages_for_api = [
                        {"role": "system", "content": system_prompt},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ]
                    
                    response = oai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages_for_api,
                        tools=tools,
                        stream=True,
                    )
                    
                    # Variables to accumulate the response
                    full_response = ""
                    function_calls = {}
                    
                    # Process the streaming response
                    for chunk in response:
                        delta = chunk.choices[0].delta
                        
                        # Handle regular content
                        if delta.content:
                            full_response += delta.content
                            message_placeholder.markdown(full_response + "▌")
                        
                        # Handle tool calls
                        if delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                index = tool_call.index
                                
                                if index not in function_calls:
                                    function_calls[index] = {
                                        "id": tool_call.id or "",
                                        "type": tool_call.type or "",
                                        "function": {
                                            "name": tool_call.function.name or "",
                                            "arguments": tool_call.function.arguments or ""
                                        }
                                    }
                                else:
                                    # Append arguments as they come in
                                    if tool_call.function.arguments:
                                        function_calls[index]["function"]["arguments"] += tool_call.function.arguments
                    
                    # Process function calls if any
                    if function_calls:
                        function_call_info = list(function_calls.values())[0]
                        function_name = function_call_info["function"]["name"]
                        function_args = json.loads(function_call_info["function"]["arguments"])
                        
                        # Show function call info
                        message_placeholder.markdown(f"**Function called**: `{function_name}`\n\nProcessing...")
                        
                        # Execute the function
                        if function_name == "send_email":
                            try:
                                email_request = SendEmailRequest(
                                    email=function_args["email"],
                                    subject=function_args["subject"],
                                    body=function_args["body"]
                                )
                                result = send_email(email_request)
                                function_result = f"Email sent successfully: {result}"
                            except Exception as e:
                                function_result = f"Error sending email: {str(e)}"
                        else:
                            function_result = f"Unknown function: {function_name}"
                        
                        # Store function call and result
                        function_call_msg = {
                            "role": "assistant",
                            "content": "",
                            "function_call": function_call_info,
                            "function_result": function_result
                        }
                        st.session_state.messages.append(function_call_msg)
                        
                        # Add function call to RecallrAI session
                        # session.add_assistant_message(f"Function call: {function_name} with args: {function_args}")
                        
                        # Call the model again with the function result
                        messages_for_api.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": function_call_info["id"],
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": function_call_info["function"]["arguments"]
                                }
                            }]
                        })
                        
                        messages_for_api.append({
                            "role": "tool",
                            "tool_call_id": function_call_info["id"],
                            "content": function_result
                        })
                        
                        # Get final response from OpenAI
                        final_response = oai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages_for_api,
                        )
                        
                        final_content = final_response.choices[0].message.content
                        message_placeholder.markdown(final_content)
                        
                        # Save to session state and RecallrAI
                        st.session_state.messages.append({"role": "assistant", "content": final_content})
                        session.add_assistant_message(final_content)
                    else:
                        # If no function calls, just display the regular response
                        message_placeholder.markdown(full_response)
                        
                        # Save the assistant's response to session state and RecallrAI session
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        session.add_assistant_message(full_response)
                
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    message_placeholder.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
