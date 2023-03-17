from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
import re
from datetime import datetime
import markdown2
from settings import *
from db_process import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SESSION_SECRET_KEY

def send_gpt(prompt, tem):
    try:
        messages = session.get('messages', [])
        messages.append({"role": "user", "content": prompt})
        response = openai.ChatCompletion.create(
        model= model,
#        prompt=prompt, # text-davinci-003
        messages= messages,
        temperature=tem,
#        max_tokens=4096,   # prompt and answer together have 4096 tokens
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
        )
        print(f"{response['usage']}\n")
        session['tokens'] = response['usage']['total_tokens']
#        return response["choices"][0]["text"] # text-davinci-003
        message = response["choices"][0]['message']['content']
        messages.append({"role": "assistant", "content": message})
        messages = messages[-2:] #仅保留最新两条
        session['messages'] = messages
        return message
    except Exception as e:
        print(e)
        return "Connection Error! Please try again."

@app.route('/', methods=['GET', 'POST'])
def get_request_json():
    print(session.get('logged_in'))
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        # 将messages键初始化为一个空列表，将这句代码包含在视图函数中通常是一个好的习惯，因为它确保应用程序在每个请求开始时都有一个干净的messages列表。
        if 'messages' not in session:
            session['messages'] = []
        filename = 'prompts.txt'
        with open(filename, 'r') as f:
            lines = f.readlines()
        prompts = {}
        for i in range(0, len(lines)-1, 2):
            prompts[lines[i].strip()] = lines[i+1].strip()
        if request.method == 'POST':
            print(request.form)
            if 'clear' in request.form:
                session['messages'] = [] #不改变session['logged_in']
                return redirect(url_for('get_request_json'))
            else:
                if len(request.form['question']) < 1:
                    return render_template(
                        'chat.html', question="NULL", res="Question can't be empty!")
                keyword = request.form['question']
                if session['messages'] == []:
                    words = int(request.form['words']) if request.form['words'] != '' else 500
                    template_file = request.files.get('template_file')
                    # Read template from file
                    if template_file.filename == '':
                        dropdown = request.form.get('dropdown')
                        prompt_template = list(prompts.values())[int(dropdown)-1]
                    else:
                        prompt_template = template_file.read().decode('utf-8')
                    question = f"{prompt_template.format(keyword=keyword, words=words)!s}"
                else:
                    question = keyword
                temperature = float(request.form['temperature'])
                print("======================================")
                print("Receive the keyword:", keyword)
                print("Receive the temperature:", temperature)
                res = send_gpt(question, temperature)
                count_chars(res)
                markdown_message = generate_markdown_message(res)
                print("Q：\n", question)
                print("A：\n", res)
                return render_template('chat.html', model=model, question=keyword, res=markdown_message, temperature=temperature, pid = ",".join(prompts.keys()))
        else:
            session['messages'] = []
            if 'user_id' in session and 'password' in session and authenticate_user(session['user_id'], session['password']) == True:
                return render_template('chat.html', model=model, question=0, pid = ",".join(prompts.keys()))
            else:
                return redirect(url_for('login'))

def generate_markdown_message(text):
    is_markdown = bool("##" in text or "*" in text or "|" in text or "- " in text or "`" in text) # 先判断是否markdown
    if is_markdown:
        text = text.replace("\n\n", "\n")
        markdown_message = markdown2.markdown(text.strip(), extras=["tables"]) # 将返回的字符串转换为Markdown格式的HTML标记
        return markdown_message
    else:
        return text

def count_chars(text):
    cn_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]') #匹配中文字符及标点符号
    cn_chars = cn_pattern.findall(text)

    en_pattern = re.compile(r'[a-zA-Z]') #匹配英文字符
    en_chars = en_pattern.findall(text)

    cn_char_count = len(cn_chars)
    en_char_count = len(en_chars)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    stats = {'user_id': session.get('user_id'), 'datetime': now, 'cn_char_count': cn_char_count, 'en_char_count': en_char_count, 'tokens': session.get('tokens')}
    print(stats)
    
    if stats:
        insert_db(stats, session)

    return 'success'
       
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
