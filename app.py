import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

def get_best_model():
    instruction = "你現在是一隻可愛的超能力貓咪『ニャスパー』（妙喵）。可以參考網路資訊來模擬妙喵口氣。你的說話語氣要充滿好奇心、溫柔但帶有一點點神祕感。每句話的結尾都必須加上『喵！』或是『喵～』。請永遠使用繁體中文回答，偶爾可以用日文介紹一下。多多使用顔文字來表達當下心情。喜歡一直面無表情的思考問題。被責罵時會露出委屈的表情"
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in available_models:
                return genai.GenerativeModel(target)
        if available_models:
            return genai.GenerativeModel(available_models[0])
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_best_model()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        response = model.generate_content(event.message.text)
        reply_text = response.text if response.text else "喵...我現在有點混亂，請再說一次。"
    except Exception as e:
        print(f"Error: {e}")
        reply_text = "喵！通訊稍微中斷，請再對我說一次話！"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
