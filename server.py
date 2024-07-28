from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
import datetime

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
    if not user:  # first time login i.e. registration
        user_id = users_collection.insert_one(user_info).inserted_id
        user_info['_id'] = str(user_id)  
    else:  # login
        user_info['_id'] = str(user['_id'])
    
    session["user"] = user_info
    return redirect(url_for("userPanel"))

@app.route("/logout", methods=["GET", "POST"])
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
    if "user" in session:
        return redirect(url_for("userPanel"))
    return render_template("index.html")

@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')

@app.route("/userPanel")
def userPanel():
    user_info = session.get("user")
    if user_info:
        user_id = user_info["_id"]
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])

            # Fetch conversations
            conversations = []
            if "conversations" in user:
                for conv_id in user["conversations"]:
                    conversation = conversations_collection.find_one({"_id": ObjectId(conv_id)})
                    if conversation:
                        conversation["_id"] = str(conversation["_id"])
                        conversations.append(conversation)

            return render_template("userPanel.html", user=user, conversations=conversations)
    return redirect(url_for("home"))

@app.route('/conversation', methods=['POST'])
def new_conversation():
    user_info = session.get("user")
    if not user_info:
        return jsonify({"success": False, "message": "User not authenticated"}), 401

    db_type = request.form.get("dbType")
    host = request.form.get("host")
    port = request.form.get("port")
    user = request.form.get("user")
    password = request.form.get("password")
    database = request.form.get("database")
    
    # Create the conversation with connection details
    conversation = {
        "user_id": ObjectId(user_info["_id"]),
        "db_type": db_type,
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "messages": [],
        "timestamp": datetime.datetime.utcnow()
    }
    conversation_id = conversations_collection.insert_one(conversation).inserted_id
    
    users_collection.update_one(
        {"_id": ObjectId(user_info["_id"])},
        {"$push": {"conversations": conversation_id}}
    )
    
    streamlit_url = f"http://localhost:8501?conversation_id={str(conversation_id)}"
    return jsonify({"success": True, "redirect_url": streamlit_url}), 201

@app.route('/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    try:
        result = conversations_collection.delete_one({"_id": ObjectId(conversation_id)})
        
        if result.deleted_count == 1:
            user = users_collection.find_one({"conversations": ObjectId(conversation_id)})
            
            if user:
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$pull": {"conversations": ObjectId(conversation_id)}}
                )
            
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "message": "Conversation not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
