from google.cloud import vision
from google.oauth2 import service_account
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from boto3.dynamodb.conditions import Key
import boto3
import base64
import json
import openai
import os

LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
OPENAI_ORGANIZATION = os.getenv('OPENAI_ORGANIZATION')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
token_count = boto3.resource('dynamodb').Table('openai-token-count')
word_picker_db = boto3.resource('dynamodb').Table('word-picker')

def get_image(message_id):
    message_content = line_bot_api.get_message_content(message_id)
    with open(f'/tmp/{message_id}.jpg', 'wb') as f:
        f.write(message_content.content)

def detect_text(message_id):
    credentials = service_account.Credentials.from_service_account_file('./key.json')
    client = vision.ImageAnnotatorClient(credentials=credentials)
    with open(f'/tmp/{message_id}.jpg', 'rb') as image_file:
        content = image_file.read()
    b64_data = base64.b64encode(content).decode('utf-8')
    image = vision.Image(content=b64_data)
    response = client.document_text_detection(image=image)
    texts = response.text_annotations
    text = texts[0]
    txt = text.description
    return txt

def chat_completion(text, content, user_id):
    openai.organization = OPENAI_ORGANIZATION
    openai.api_key = OPENAI_API_KEY
    openai.Model.list()
    config = 'テキストの中から以下の「項目名」に該当する言葉を抜き出して、項目ごとに出力してください。\n'
    content = f'項目名：\n{content}'
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": config + content},
            {"role": "user", "content": text}
            ]
        )
    token_count.put_item(
        Item={
            'name': user_id,
            'id': completion['id'],
            'created': completion['created'],
            'prompt_tokens': completion['usage']['prompt_tokens'],
            'completion_tokens': completion['usage']['completion_tokens'],
            'total_tokens': completion['usage']['total_tokens']
        }
    )
    return completion['choices'][0]['message']['content']

def lambda_handler(event, context):
    message = json.loads(event['body'])['events'][0]
    if message['message']['type'] == 'text':
        if message['message']['text'] == '項目設定':
            reply_token = message['replyToken']
            text = 'テキスト入力画面を開き、抽出したい項目名をテキストで送信してください。'
            line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
        elif message['message']['text'] == '現在の設定':
            user_id = message['source']['userId']
            reply_token = message['replyToken']
            res = word_picker_db.query(KeyConditionExpression=Key('user_id').eq(user_id))
            item = max(res['Items'], key=(lambda x:x['timestamp']))
            text = item['content']
            line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
        elif message['message']['text'] == '利用方法':
            reply_token = message['replyToken']
            text = '【利用方法】\n1．メニューで「読み取り項目を設定する」を選択。\n2．テキスト入力欄を開き、抽出したい項目を箇条書きで入力して送信する。\n　例）名前、住所、生年月日　など\n3．ワードを抽出する対象の画像を送信する。\n　※送信された画像は保存しません。'
            line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
        else:
            user_id = message['source']['userId']
            timestamp = message['timestamp']
            reply_token = message['replyToken']
            content = message['message']['text']
            word_picker_db.put_item(
                Item={
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'content': content
                }
            )
            text = '項目を設定しました。ワードを抽出する対象の画像を送信してください。'
            line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
    elif message['message']['type'] == 'image':
        user_id = message['source']['userId']
        message_id = message['message']['id']
        reply_token = message['replyToken']
        try:
            get_image(message_id)
            text = detect_text(message_id)
            res = word_picker_db.query(KeyConditionExpression=Key('user_id').eq(user_id))
            item = max(res['Items'], key=(lambda x:x['timestamp']))
            content = item['content']
            reply_message = chat_completion(text, content, user_id)
            ok_json = {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": {},
                "body": ""
            }
            line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_message))
            for f in os.listdir('/tmp/'):
                os.remove(os.path.join('/tmp/', f))
            return ok_json
        except:
            error_json = {
                "isBase64Encoded": False,
                "statusCode": 500,
                "headers": {},
                "body": "Error"
            }
            text = 'エラーが発生しました。\n画像を送信したい場合は、テキストが含まれた画像を再送してみてください。'
            line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
            for f in os.listdir('/tmp/'):
                os.remove(os.path.join('/tmp/', f))
            return error_json