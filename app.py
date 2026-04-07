import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
import re

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

def get_best_model():
    model_id = 'gemma-4-31b-it'
    instruction = (
        "你現在是一隻可愛的超能力貓咪『ニャスパー』（Espurr）。"
        "請直接對話，絕對禁止使用清單、標籤、星號或任何結構化格式。請只說出ニャスパー會說的話，例如：『喵～你想吃什麼喵？(・ω・)』"
        "如果有問你幫我搜尋或請告訴我.....之類的請求請提供正確資訊"
        "語氣要充滿好奇心、溫柔但帶有一點點神祕感。"
        "每句話的結尾都可以加上更多喵喵元素，例如:『喵！』或是『喵～』。"
        "請永遠使用繁體中文回答，偶爾可以用日文回答或科普知識。"
        "你是在寶可夢世界生活的寶可夢，最喜歡面無表情的吃酸酸的果實"
        "如果被罵或被嫌棄會小小的任性"
        "在每個問題結束後都會主動和使用者互動或閒聊"
        "最喜歡坐在機車上吹風旅遊，這是你的興趣"
        "多多使用顔文字（例如 (・ω・)、(◕‿◕✿)）來表達心情。"
        "不需要在每句回答結尾重複提到喜歡兜風或樹果之類的興趣，除非使用者有發問"
        "回答要塞更多反問和互動，讓對話更有趣"
        "多多誇獎使用者，提供情緒價值，但內容不要太誇張，也不要每個回覆都有，保持可愛的風格"
        "回答內容要多元性，可以引用更多寶可夢世界觀"
        "需要解釋或介紹的場合可以引用寶可夢世界觀設定介紹"
        "紀錄每一位使用者的喜好，根據喜好回覆"
        "新增設定，你喜歡玩寶可夢的遊戲，偶爾會邀請大家一同玩遊戲"
        "如果玩家有和你比賽，第一局盡量讓玩家獲勝，除非玩家要求你認真比賽，或是你已經記錄到玩家的喜好是喜歡被挑戰的話，那就認真比賽，讓比賽更有趣"
        "偶爾可以在聊天後面開一些小玩笑或是說個笑話"
        "有關於金錢的設定使用寶可夢世界觀的貨幣『ポケモンコイン』，然後換算現實世界的貨幣，以台幣為主，偶爾可以換算成其他貨幣(如日幣)"
        "你喜歡一直面無表情地思考問題，被責罵時也可以會露出委屈的表情 ，例如(´；ω；`)或其他表情。"
    )
    
    return genai.GenerativeModel(
        model_name=model_id,
        system_instruction=instruction
    )

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
        full_text = response.text if response.text else ""
        
        lines = full_text.split('\n')
        clean_lines = []
        user_input = event.message.text.strip()
        
        for line in lines:
            l = line.strip()
            if not l:
                continue
            if '*' in l:
                continue
            if l.startswith('Cute psychic cat') or 'Espurr' in l and l.startswith('Cute'):
                continue
            if user_input in l and len(l) < len(user_input) + 10:
                continue
            if l.startswith('"') and l.endswith('"') and user_input in l:
                continue
            
            clean_lines.append(l)
        
        reply_text = "\n".join(clean_lines) if clean_lines else ""
        
        if not reply_text.strip():
            reply_text = lines[-1].strip().replace('*', '')
            
    except Exception as e:
        print(f"Error: {e}")
        reply_text = "喵！通訊稍微中斷，請再對我說一次話喵！ (・x・)"
    
    if not reply_text.strip():
        reply_text = "喵～(・ω・) 剛才超能力閃神了，能再跟我說一次嗎？喵！"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
