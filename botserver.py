from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
from services.faq_handler import FAQHandler

app = Flask(__name__)

load_dotenv()

# Your LINE channel credentials
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# Configure LINE API client
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize handlers
faq_handler = FAQHandler(model_name="gemini-pro", faq_path="data/faq.json")

# Store conversation history
conversation_history = {}

@app.route("/callback", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # Handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print("Message received from LINE")
    user_id = event.source.user_id
    user_message = event.message.text
    
    # Initialize conversation history for new users
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Get message count for this user
    message_count = len(conversation_history[user_id])
    
    start_time = time.time()
    
    # Generate response
    response, resp_type = faq_handler.generate_response(
        user_message, 
        message_count=message_count
    )
    
    # Update conversation history
    conversation_history[user_id].append((response, resp_type))
    
    print(f"Response generated in {time.time() - start_time} seconds")
    
    # Send response using the new LINE SDK
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )
    
    # Cleanup old conversations (optional)
    if len(conversation_history.get(user_id, [])) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]

if __name__ == "__main__":
    app.run(port=8000, debug=True)