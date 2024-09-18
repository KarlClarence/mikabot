from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit
import time
from datetime import timedelta
import openai  # 使用openai库，但配置为Azure的API
import traceback
from openai_token_counter import openai_token_counter
import configparser
import time
import os
from openai import AzureOpenAI
# 读取配置文件
config = configparser.ConfigParser()
config.read("bot.conf")

# 读取prompt文件内容
prompt = open(config["bot"].get("prompt_file", "mika.txt"), encoding="utf-8").read()
original_messages = [
    {"role": "system", "content": prompt},
    {"role": "assistant", "content": "Sensei欢迎回来！\\我可是个乖乖看家的好孩子哦"}
]
messages = original_messages.copy()
lastMessageTime = 0
inputLock = False

# 配置Azure OpenAI API
openai.api_key = config["openai"]["api_key"]
openai.api_base = config["openai"].get("api_url")
model_name = config["openai"].get("model", "gpt-4o")

def countToken():
    return openai_token_counter(messages=messages, model="gpt-4")


def getTimeStr():
    return time.strftime("%Y/%m/%d %a %H:%M:%S", time.localtime())


# status: 0:receive, 1:response, 2:end, 3:single
def send(msg, stat):
    emit('e', {'r': msg, 's': stat})


def handleMessage(msg):
    global messages, inputLock, lastMessageTime
    inputLock = True
    print("recv: " + msg)
    if msg == "cls":
        send("chat history clear.\\nTokens usage: " + str(countToken()), 3)
        messages = original_messages.copy()
        inputLock = False
        lastMessageTime = 0
        return
    elif msg == "tokens":
        send("Tokens usage: " + str(countToken()), 3)
        inputLock = False
        return
    try:
        if time.time() - lastMessageTime > 60 * 10:
            messages.append({"role": "system", "content": "下面的对话开始于 " + getTimeStr()})
            send(getTimeStr(), 0)
        else:
            send("", 0)
        lastMessageTime = time.time()
        messages.append({"role": "user", "content": msg})

        # Updated API usage for OpenAI SDK >= 1.0.0
        stream = openai.chat.completions.create(
            model= "gpt-4o",
            messages=messages,
            stream=True,
            timeout=60
        )

        content = ""
        last_len = 1
        for chunk in stream:
            content += chunk.choices[0].delta.content or ""
            l = content.split("\\")
            if len(l) > last_len:
                for i in l[last_len - 1:-1]:
                    send(i, 1)
                    time.sleep(0.2)
                last_len = len(l)
        send(l[-1], 2)
        messages.append({"role": "assistant", "content": content})
    except Exception as e:
        send(f"Error: \\n{traceback.format_exc()}", 3)
    print(messages[1:])
    inputLock = False


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins='*')


@app.route('/')
def index():
    return send_from_directory('', 'index.html')


@app.route('/history')
def history():
    return messages[1:], 200, {'Content-Type': 'application/json'}


@socketio.on('connect', namespace='/chat')
def test_connect():
    print('Client connected')


@socketio.on('e', namespace='/chat')
def handle_message(message):
    if inputLock:
        return
    print(message['m'])
    handleMessage(message['m'])


@socketio.on('disconnect', namespace='/chat')
def test_disconnect():
    print('Client disconnected')


socketio.run(app, host=config["server"].get("listen", "0.0.0.0"),
             port=config["server"].get("port", "80"), allow_unsafe_werkzeug=True)
