from dotenv import load_dotenv
import os
from flask import Flask
from flask_cors import CORS
from waitress import serve
from app.controllers.product_controller import product_controller

app = Flask(__name__)
load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL")
CORS(app, origins=[FRONTEND_URL])

app.register_blueprint(product_controller)

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=5000)
