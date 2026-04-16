import json
import urllib.request

import boto3

class TelegramBot(object):
    def __init__(self, config: dict):
        self.secret_name = config["aws"]["secret_name"]
        self.region_name = config["aws"]["region_name"]

    def _get_secret(self):
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=self.region_name)
        secret = json.loads(client.get_secret_value(SecretId=self.secret_name)['SecretString'])
        return (secret['TELEGRAM_BOT_TOKEN'], secret['TELEGRAM_CHANNEL_ID'])

    def send_telegram_message(self, text):
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = self._get_secret()
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
