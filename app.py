from flask import Flask, request, render_template, session, redirect
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
# 将messages键初始化为一个空列表，将这句代码包含在视图函数中通常是一个好的习惯，因为它确保应用程序在每个请求开始时都有一个干净的messages列表。
    if 'messages' not in session:
        session['messages'] = []
    if request.method == 'POST':
        if len(request.form['question']) < 1:
            return render_template(
                'chat.html', question="NULL", res="Question can't be empty!")
        keyword = request.form['question']
        if session['messages'] == []:
            words = int(request.form['words'])
            template_file = request.files.get('template_file')
            # Read template from file
            if template_file.filename == '':
                filename = 'prompt.txt'
                with open(filename, 'r') as f:
                    prompt_template = f.read()
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
        return render_template('chat.html', model=model, question=keyword, res=str(res), temperature=temperature)
    else:
        session.clear()
        return render_template('chat.html', model=model, question=0)

