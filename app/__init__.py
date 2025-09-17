from flask import Flask
import os
import secrets

folders = ["/app/app/static/media/videos", "/app/app/static/media/images"]
for folder in folders:
    if not os.path.exists(folder):
        os.mkdir(folder)

app = Flask(__name__, static_url_path="/static")
# Use environment variable for secret key, with secure fallback
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
from app import routes
