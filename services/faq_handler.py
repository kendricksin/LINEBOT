import json
import google.generativeai as genai

class FAQHandler:
    def __init__(self, model_name="gemini-pro", faq_path="data/faq.json"):
        self.model_name = model_name
        with open(faq_path, 'r', encoding='utf-8') as f:
            self.faq_data = json.load(f)
        self.model = genai.GenerativeModel(model_name=self.model_name)

    def _analyze_message(self, user_message):
        """Analyze message to determine language and query type"""
        analysis_prompt = f'''Analyze this message: "{user_message}"

Return ONLY a JSON object in this EXACT format:
{{
    "language": "en or th or ja or zh",
    "query_type": "location or menu or hours or booking or parking or other",
    "original_message": "the original message"
}}

Rules:
- language must EXACTLY match the user's language
- If message contains Thai script, language MUST be "th"
- If message contains Japanese characters, language MUST be "ja"
- If message contains only Chinese characters, language MUST be "zh"
- query_type must match the most relevant category
- For greetings or unclear messages, use query_type "other"

Reply with ONLY the JSON object, no other text.'''

        try:
            response = self.model.generate_content(analysis_prompt)
            cleaned_response = response.text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:-3]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:-3]
            return json.loads(cleaned_response)
        except Exception as e:
            print(f"Error in message analysis: {e}")
            return {
                "language": "en",
                "query_type": "other",
                "original_message": user_message
            }

    def _format_response_with_personality(self, base_response, language):
        """Format the FAQ response with a friendly personality"""
        personality_prompt = f'''Make this response more friendly and conversational, keeping the same information but adding warmth:

Original response: {base_response}

Rules:
- Keep the same language as original
- Maintain all factual information
- Add friendly tone and warmth
- For Thai: use polite particles ค่ะ/ครับ appropriately
- For Japanese: maintain formal politeness
- Keep it concise

Response:'''

        try:
            response = self.model.generate_content(personality_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in personality formatting: {e}")
            return base_response

    def _get_response(self, query_type, language):
        """Get response from FAQ data and format it"""
        # Default responses for when query_type is "other"
        other_responses = {
            "en": "Hello! How can I help you today?",
            "th": "สวัสดีค่ะ มีอะไรให้ช่วยไหมคะ?",
            "ja": "いらっしゃいませ。ご用件は何でしょうか？",
            "zh": "您好！请问有什么可以帮您？"
        }

        # Get base response from FAQ or default
        base_response = (self.faq_data.get(query_type, {}).get(language) 
                        or other_responses.get(language, other_responses["en"]))
        
        # Format with personality
        return self._format_response_with_personality(base_response, language)

    def generate_response(self, user_message, message_count=0):
        """Generate response using analyzed message and FAQ data"""
        # First analyze the message
        analysis = self._analyze_message(user_message)
        print(f"Analyzed message: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
        
        # Handle message count limit
        if message_count >= 3:
            handoff_messages = {
                "en": "I'd love to help you more! Let me have our staff contact you directly with more detailed information.",
                "th": "ยินดีให้ข้อมูลเพิ่มเติมค่ะ ขออนุญาตให้พนักงานของเราติดต่อกลับนะคะ",
                "ja": "より詳しい情報をご提供させていただきたく、スタッフから直接ご連絡させていただきます。",
                "zh": "很乐意为您提供更多帮助！让我们的工作人员直接联系您，提供更详细的信息。"
            }
            return handoff_messages[analysis["language"]], "handoff"

        try:
            # Get formatted response
            response = self._get_response(
                analysis["query_type"], 
                analysis["language"]
            )
            return response, "faq" if analysis["query_type"] != "other" else "other"
            
        except Exception as e:
            print(f"Error generating response: {e}")
            error_messages = {
                "en": "I apologize, but I'm having trouble right now. Please try again!",
                "th": "ขออภัยค่ะ ระบบขัดข้องชั่วคราว กรุณาลองใหม่อีกครั้งนะคะ",
                "ja": "申し訳ございませんが、一時的なエラーが発生しました。もう一度お試しください。",
                "zh": "抱歉，系统暂时出现问题。请稍后再试！"
            }
            return error_messages[analysis["language"]], "error"