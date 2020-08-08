import os, base64, json
from firebase_admin import credentials
import firebase_admin

def base64_to_json(base64_str):
    return json.loads(base64.b64decode(base64_str))

CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
FIREBASE_ADMIN_JSON = base64_to_json(os.getenv('FIREBASE_ADMIN_JSON_BASE64'))

CERTIFICATE = credentials.Certificate(FIREBASE_ADMIN_JSON)

INTERVAL = 12

firebase_admin.initialize_app(CERTIFICATE)