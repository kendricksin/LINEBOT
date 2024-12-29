from flask import Flask, request
from pymessenger import Bot
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

app = Flask(__name__)

load_dotenv()

# Your Facebook credentials
PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('FB_VERIFY_TOKEN')

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

# Initialize Facebook Messenger bot
messenger = Bot(PAGE_ACCESS_TOKEN)

def get_gemini_response(prompt):
    try:
        # Create a chat completion using the Gemini API
        response = model.generate_content(prompt)
        # Extract the response text
        return response.text
    except Exception as e:
        print(f"Error in getting Gemini response: {e}")
        return "Sorry, I encountered an error processing your request."

@app.route("/webhook", methods=['GET'])
def verify_webhook():
    # Webhook verification for Facebook
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

@app.route("/webhook", methods=['POST'])
def webhook():
    data = request.get_json()
    print("Received message:", data)

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    try:
                        message_text = messaging_event["message"]["text"]
                        
                        print("Calling Gemini API...")
                        start_time = time.time()
                        gemini_response = get_gemini_response(message_text)
                        print(f"Gemini response received in {time.time() - start_time} seconds")
                        
                        print("Sending response back to Messenger")
                        messenger.send_text_message(sender_id, gemini_response)
                        
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        messenger.send_text_message(sender_id, "Sorry, I encountered an error processing your message.")

    return "OK", 200

if __name__ == "__main__":
    app.run(port=8000, debug=True)