import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# 設定你的金鑰 (Render 會自動從環境變數抓取)
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

# 設定大腦模型 - 使用最穩定的名稱
model = genai.GenerativeModel('gemini-pro')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.event_log
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 妙喵開始思考
    try:
        response = model.generate_content(event.message.text)
        reply_text = response.text
    except Exception as e:
        reply_text = "喵... 我的大腦打結了，請稍後再試！"
        print(f"Error: {e}")
    
    # 回傳給使用者
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
