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
conversations_collection = db["conversations"]

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
    if not user:#first time login i.e. registration
        user_id = users_collection.insert_one(user_info).inserted_id
        user_info['_id'] = str(user_id)  
    else:#login
        user_info['_id'] = str(user['_id'])
    
    session["user"] = user_info
    return redirect(url_for("userPanel"))

@app.route("/logout",methods=["GET", "POST"])
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
    
@app.route("/userPanel")
def userPanel():
    user_info = session.get("user")
    if user_info:
        user_id = user_info["_id"]
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            return render_template("userPanel.html", user=user)
    return redirect(url_for("home"))#userPanel failed i.e user not found but login successfull
    
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("userPanel"))
    return render_template("index.html")

@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
