from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify, Response, stream_with_context
import re
import json
import requests
import uuid
from datetime import datetime
from settings import *
from db_process import *
from md_process import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SESSION_SECRET_KEY # SECRET_KEY是Flask用于对session数据进行加密和签名的一个关键值。如果没有设置将无法使用session

timeout_streaming = 5
global_messages = []
stream_data = {}

def get_prompt_templates():
    filename = 'prompts.txt'
    with open(filename, 'r') as f:
        lines = f.readlines()
    prompts = {}
    for i in range(0, len(lines)-1, 2):
        prompts[lines[i].strip()] = lines[i+1].strip()
    return prompts

def generate_text(prompt, tem, messages):
    try:
        messages.append({"role": "user", "content": prompt})
        print("generate_text:", messages)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }

        # history = [construct_system(system_prompt), *history]

        payload = {
            "model": model,
            "messages": messages,  # [{"role": "user", "content": f"{inputs}"}],
            "temperature": tem,  # 1.0,
            "n": 1,
            "stream": True,
            "presence_penalty": 0,
            "frequency_penalty": 0,
        }
        timeout = timeout_streaming

        response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=timeout)
        return response

    except Exception as e:
        print(e)
        return "Connection Error! Please try again."

def send_gpt(prompt, tem, messages, user_id, tokens):
    global global_messages
    token_counter = 0
    partial_words = ""
    response = generate_text(prompt, tem, messages)
    
    # 添加如下调试信息
    # print("Response:", response)
    # print("Response status code:", response.status_code)
    # print("Response headers:", response.headers)

    for chunk in response.iter_lines():
        if chunk:
            chunk = chunk.decode()
            # print("Decoded chunk:", chunk)  # 添加这一行以打印解码的块
            chunklength = len(chunk)
            data = json.loads(chunk[6:])
            # print(data['choices'][0]["delta"])
            try:
                if chunklength > 6 and "delta" in data['choices'][0]:
                    finish_reason = data['choices'][0]['finish_reason']
                    if finish_reason == "stop":
                        break
                    if "content" in data['choices'][0]["delta"]:
                        partial_words += data['choices'][0]["delta"]["content"]
                        # print("Content found:", partial_words)  # 添加这一行以打印找到的内容
                        token_counter += 1
                        yield {'content': partial_words}
                    else:
                        print("No content found in delta:", data['choices'][0]["delta"])  # 添加这一行以打印没有内容的 delta
                else:
                    pass
            except json.JSONDecodeError:
                pass

#        print(f"{response['usage']}\n")
#        session['tokens'] = response['usage']['total_tokens']
    # messages = messages
    messages.append({"role": "assistant", "content": partial_words})
    print("精简前messages:", messages)
    messages = messages[-2:] #仅保留最新两条
    global_messages = messages

    tokens = token_counter
    count_chars(partial_words, user_id, tokens)
    return {'messages': messages}
        
def count_chars(text, user_id, tokens):
    cn_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]') #匹配中文字符及标点符号
    cn_chars = cn_pattern.findall(text)

    en_pattern = re.compile(r'[a-zA-Z]') #匹配英文字符
    en_chars = en_pattern.findall(text)

    cn_char_count = len(cn_chars)
    en_char_count = len(en_chars)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 获取 session 中的统计结果列表，如果不存在则初始化为空列表
    # results = session.get('results', [])
    # 将当前统计结果添加为字典
    stats = {'user_id': user_id, 'datetime': now, 'cn_char_count': cn_char_count, 'en_char_count': en_char_count, 'tokens': tokens}
    print(stats)
    
    if stats:
        insert_db(stats, user_id, global_messages)

    return 'success'

@app.route('/', methods=['GET', 'POST'])
def get_request_json():
    global global_messages
    prompts = get_prompt_templates()
    if request.method == 'POST':
        if 'clear' in request.form:
            global_messages = [] #不改变session['logged_in']
            return redirect(url_for('get_request_json'))
        else:
            return render_template('chat.html', model=model, user_id=session.get('user_id'), pid=",".join(prompts.keys()))
    else:
        global_messages = []
        if 'user_id' in session and 'password' in session and authenticate_user(session['user_id'], session['password']) == True:
            return render_template('chat.html', model=model, user_id=session.get('user_id'), question=0, pid = ",".join(prompts.keys()))
        else:
            return redirect(url_for('login'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            session.update(logged_in=True, user_id=username, password=password)
            return redirect(url_for('get_request_json'))
        else:
            flash('用户名或密码错误')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    # session.pop('logged_in', None)
    session.clear()
    return redirect(url_for('get_request_json'))

@app.route('/update-session', methods=['POST'])
def update_session():
    session['logged_in'] = True  # 根据您的实际需求更新会话状态
    return jsonify({'success': True})

@app.route('/stream_get/<unique_url>', methods=['GET'])
def stream_get(unique_url):
    if unique_url in stream_data:
        response_data = stream_data[unique_url]['response']
        # del stream_data[unique_url]
        return Response(response_data, content_type='text/event-stream')
    else:
        return "Error: Invalid URL", 400

@app.route('/stream', methods=['POST'])
def stream():
    prompts = get_prompt_templates()

    if len(request.form['question']) < 1:
        return redirect(url_for('get_request_json'))

    keyword = request.form['question']
    if global_messages == []:
        words = int(request.form['words']) if request.form['words'] != '' else 500
        template_file = request.files.get('template_file')
        if not template_file:
            dropdown = request.form.get('dropdown')
            prompt_template = list(prompts.values())[int(dropdown) - 1]
        else:
            prompt_template = template_file.read().decode('utf-8')
        question = f"{prompt_template.format(keyword=keyword, words=words)!s}"
    else:
        question = keyword

    temperature = float(request.form['temperature'])
    messages = global_messages
    user_id = session.get('user_id')
    tokens = session.get('tokens')
    def process_data():
        for res in send_gpt(question, temperature, messages, user_id, tokens):
            if 'content' in res:
                markdown_message = generate_markdown_message(res['content'])
                # print(f"Yielding: {markdown_message}")  # 添加这一行
                yield f"data: {json.dumps({'data': markdown_message})}\n\n" # 将数据序列化为JSON字符串
                
    if stream_data:
        stream_data.pop(list(stream_data.keys())[0])  # 删除已使用的URL及相关信息              
    unique_url = uuid.uuid4().hex
    stream_data[unique_url] = {
        'response': process_data(),
        'messages': global_messages,
    }
    print(session)
    session['tokens'] = 0
    return 'stream_get/' + unique_url                
