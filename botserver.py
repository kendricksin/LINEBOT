from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

app = Flask(__name__)

load_dotenv()

# Your LINE channel credentials
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def get_gemini_response(prompt):
    try:
        # Create a chat completion using the Gemini API
        response = model.generate_content(prompt)
        # Extract the response text
        return response.text
    except Exception as e:
        print(f"Error in getting Gemini response: {e}")
        return "Sorry, I encountered an error processing your request."

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("Message received from LINE")
    user_message = event.message.text
    
    print("Calling Gemini API...")
    start_time = time.time()
    gemini_response = get_gemini_response(user_message)
    print(f"Gemini response received in {time.time() - start_time} seconds")
    
    print("Sending response back to LINE")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=gemini_response)
    )

if __name__ == "__main__":
    app.run(port=8000, debug=True)