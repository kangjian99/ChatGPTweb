import pyodbc
    
def authenticate_user(username, password):
    # 连接到 Azure SQL 数据库，并检查 user_info 表格中是否存在提供的用户名和密码
    cnxn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={db_username};PWD={db_password}')
    cursor = cnxn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_info WHERE user_id = ? AND password = ?", (username, password))
    count = cursor.fetchone()[0]

    # 关闭数据库连接
    cursor.close()
    cnxn.close()

    # 如果找到匹配的用户名和密码，则返回 True，否则返回 False
    return count == 1

def insert_db(result, session=None):
    # 连接到数据库
    cnxn = pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={db_username};PWD={db_password}')
    
    # 获取要插入的结果数据
    now = result.get('datetime')
    user_id = result.get('user_id')
    cn_char_count = result.get('cn_char_count')
    en_char_count = result.get('en_char_count')
    tokens = result.get('tokens')

    # 构建插入语句并执行
    query = "INSERT INTO stats (user_id, datetime, cn_char_count, en_char_count, tokens) VALUES (?, ?, ?, ?, ?);"
    params = (user_id, now, cn_char_count, en_char_count, tokens)
    cursor = cnxn.cursor()
    cursor.execute(query, params)
    
    if session:
        question = session.get('question')
        words = session.get('words')
        dropdown = session.get('dropdown')
        temperature = session.get('temperature')   
        # 构建插入语句并执行
        query = "INSERT INTO session (question, words, dropdown, temperature) VALUES (?, ?, ?, ?);"
        params = (question, words, dropdown, temperature)
        cursor = cnxn.cursor()
        cursor.execute(query, params)
        
    cnxn.commit()
    cnxn.close()