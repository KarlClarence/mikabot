from flask import Flask, request, send_from_directory, session
from flask_socketio import SocketIO, emit
import time
from datetime import timedelta
import openai
import traceback
from openai_token_counter import openai_token_counter
import configparser
import os
import sys
import uuid  # 用于生成唯一会话 ID

# 读取配置文件
config = configparser.ConfigParser()
config.read("bot.conf")

# 读取 prompt 文件内容
prompt = open(config["bot"].get("prompt_file", "mika.txt"), encoding="utf-8").read()

# 使用字典存储不同用户的对话历史
user_sessions = {}

# 配置 DeepSeek API
api_key = config["openai"]["api_key"]
base_url = "https://api.deepseek.com/v1"

client = openai.Client(  # 使用 `Client()` 替代 `OpenAI()`
    api_key=api_key,
    base_url=base_url
)

def countToken(messages):
    return openai_token_counter(messages=messages, model="deepseek-chat")

def getTimeStr():
    return time.strftime("%Y/%m/%d %a %H:%M:%S", time.localtime())

# status: 0:receive, 1:response, 2:end, 3:single
def send(msg, stat):
    emit('e', {'r': msg, 's': stat})

def handleMessage(msg, session_id):
    global user_sessions
    if session_id not in user_sessions:
        # 每个用户初始化时，创建独立的 original_messages 副本
        user_sessions[session_id] = {
            "original_messages": [
                {"role": "system", "content": prompt},
                {"role": "assistant", "content": "呐，杂鱼终于睡醒了\\快来陪我BA"}
            ],
            "messages": [],  # 当前对话历史
            "lastMessageTime": 0,
            "inputLock": False
        }
        # 初始化时，将 original_messages 复制到 messages 中
        user_sessions[session_id]["messages"] = user_sessions[session_id]["original_messages"].copy()
    user_session = user_sessions[session_id]
    user_session["inputLock"] = True
    print("recv: " + msg)
    if msg == "cls":
        send("chat history clear.", 3)
        send("Chat history clear.", 4)
        # 重置时，使用独立的 original_messages 副本
        user_session["messages"] = user_session["original_messages"].copy()
        user_session["inputLock"] = False
        user_session["lastMessageTime"] = 0
        return
    try:
        if time.time() - user_session["lastMessageTime"] > 60 * 10:
            user_session["messages"].append({"role": "system", "content": "下面的对话开始于 " + getTimeStr()})
            send(getTimeStr(), 0)
        else:
            send("", 0)
        user_session["lastMessageTime"] = time.time()
        user_session["messages"].append({"role": "user", "content": msg})

        # 调用 DeepSeek API
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=user_session["messages"],
            stream=True,
            timeout=60
        )

        content = ""
        last_len = 1
        l = [""]
        for chunk in stream:
            content += chunk.choices[0].delta.content or ""
            l = content.split("\\")
            if len(l) > last_len:
                for i in l[last_len - 1:-1]:
                    send(i, 1)
                    time.sleep(0.2)
                last_len = len(l)
        send(l[-1], 2)
        user_session["messages"].append({"role": "assistant", "content": content})
    except Exception as e:
        send(f"Error: \\n{traceback.format_exc()}", 3)
    print(user_session["messages"][1:])
    user_session["inputLock"] = False

def reset_conversation(session_id):
    global user_sessions
    if session_id in user_sessions:
        # 重置时，使用独立的 original_messages 副本
        user_sessions[session_id]["messages"] = user_sessions[session_id]["original_messages"].copy()
        user_sessions[session_id]["lastMessageTime"] = 0

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
app.secret_key = 'your_secret_key'  # 设置一个密钥用于 session
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins='*')

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/history')
def history():
    session_id = session.get('session_id')
    if session_id in user_sessions:
        return user_sessions[session_id]["messages"][:], 200, {'Content-Type': 'application/json'}
    return [], 200, {'Content-Type': 'application/json'}

@socketio.on('connect', namespace='/chat')
def test_connect():
    session_id = str(uuid.uuid4())  # 生成唯一会话 ID
    session['session_id'] = session_id
    # 初始化时，为每个用户创建独立的 original_messages 副本
    user_sessions[session_id] = {
        "original_messages": [
            {"role": "system", "content": prompt},
            {"role": "assistant", "content": "呐，杂鱼终于睡醒了\\快来陪我BA"}
        ],
        "messages": [],  # 当前对话历史
        "lastMessageTime": 0,
        "inputLock": False
    }
    # 初始化时，将 original_messages 复制到 messages 中
    user_sessions[session_id]["messages"] = user_sessions[session_id]["original_messages"].copy()
    print('Client connected with session ID:', session_id)

@socketio.on('e', namespace='/chat')
def handle_message(message):
    session_id = session.get('session_id')
    if session_id not in user_sessions or user_sessions[session_id]["inputLock"]:
        return
    print(message['m'])
    handleMessage(message['m'], session_id)

@socketio.on('disconnect', namespace='/chat')
def test_disconnect():
    session_id = session.get('session_id')
    if session_id in user_sessions:
        del user_sessions[session_id]
    print('Client disconnected with session ID:', session_id)

socketio.run(app, host=config["server"].get("listen", "0.0.0.0"),
             port=config["server"].get("port", "80"), allow_unsafe_werkzeug=True)


