from flask import Flask, request, render_template, session, redirect, flash, jsonify
import openai
import os

model = 'gpt-3.5-turbo' # or text-davinci-003
# 从环境变量中读取API密钥
openai.api_key = os.environ.get('OPENAI_API_KEY')

app = Flask(__name__, static_folder='templates/static')
app.config['SECRET_KEY'] = 'Drmhe86EPcv0fN_81Zj-nA' # SECRET_KEY是Flask用于对session数据进行加密和签名的一个关键值。如果没有设置将无法使用session
    
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
#        return response["choices"][0]["text"] # text-davinci-003
        message = response["choices"][0]['message']['content']
        messages.append({"role": "assistant", "content": message})
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
                session['messages'] == [] #不改变session['logged_in']
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
                print("Q：\n", question)
                print("A：\n", res)
                return render_template('chat.html', model=model, question=keyword, res=str(res), temperature=temperature, pid = ",".join(prompts.keys()))
        else:
            session.clear()
            return render_template('chat.html', model=model, question=0, pid = ",".join(prompts.keys()))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open('username.txt', 'r') as f:
            usernames = [line.strip() for line in f.readlines()]
        if username.lower() in [u.lower() for u in usernames] and (password == os.environ.get('Guest_PASSWORD') or os.environ.get('PASSWORD')):
            session['logged_in'] = True
            return redirect(url_for('get_request_json'))
        else:
            flash('用户名或密码错误')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('get_request_json'))

@app.route('/update-session', methods=['POST'])
def update_session():
    session['logged_in'] = True  # 根据您的实际需求更新会话状态
    return jsonify({'success': True})
