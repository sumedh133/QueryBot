from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from pymongo import MongoClient
from bson import ObjectId
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# MongoDB connection
client = MongoClient(env.get("MONGO_URI"))
db = client[env.get("MONGO_DB_NAME")]
users_collection = db["users"]

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

def serialize_user_info(user_info):
    """Convert ObjectId to string in user_info."""
    user_info['_id'] = str(user_info['_id'])
    return user_info

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )
    
@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    user_info = token['userinfo']

    user = users_collection.find_one({"sub": user_info["sub"]})
    if not user:
        user_id = users_collection.insert_one(user_info).inserted_id
        user_info['_id'] = str(user_id)  
    else:
        user_info = serialize_user_info(user)
    
    session["user"] = user_info
    return redirect("http://localhost:8501")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
    
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
