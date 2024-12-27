from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# Your LINE channel credentials
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# Your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def get_gpt_response(prompt):
    try:
        # Create a chat completion using the ChatGPT API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # You can change this to other models
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500  # Adjust based on your needs
        )
        # Extract the response text
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in getting GPT response: {e}")
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
    # Get the user's message
    user_message = event.message.text
    
    # Get response from ChatGPT
    gpt_response = get_gpt_response(user_message)
    
    # Send the response back to the user
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=gpt_response)
    )

if __name__ == "__main__":
    app.run(port=8000, debug=True)