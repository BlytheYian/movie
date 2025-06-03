from flask import Flask, render_template, request,  redirect, url_for
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv
import os

# 讀取 .env 檔
load_dotenv()

app = Flask(__name__)

# 使用環境變數建立設定
config = {
    'host': os.getenv('HOST'),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD'),
    'database': os.getenv('NAME'),
    'port': int(os.getenv('PORT', 3306))
}
# 只需初始化一次
pool = MySQLConnectionPool(pool_name="mypool",pool_size=3,**config)

#@app.route('/')：這行是 路由裝飾器，代表當用戶打開網站首頁時，Flask 會執行 index() 函數。
@app.route('/')
def index():
    return render_template('main.html')  

def search_movies(keyword):
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    field = request.args.get('field')

    if(field=="title"):
        query = f"SELECT movie_id,movie_title FROM movie WHERE movie_title LIKE %s"
    else:
        query = f"SELECT distinct movie.movie_id,movie.movie_title FROM movie inner join role on role.movie_id=movie.movie_id inner join person on role.person_id=person.person_id WHERE person.person_name LIKE %s AND role.role_type IN ('{field}');"
    like_pattern = f"%{keyword}%"  # 模糊搜尋，含有關鍵字
    cursor.execute(query, (like_pattern,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

@app.route('/search')
def search():
    keyword = request.args.get('find')  # 取得搜尋字串
    if not keyword:
        return redirect(url_for('index'))
    results = search_movies(keyword)  # 從資料庫查詢
    print(results)
    return render_template('search.html', results=results)  # 把結果丟回 main.html

def get_movie_by_code(code):
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT m.*,GROUP_CONCAT(DISTINCT CASE WHEN r1.role_type = 'director' THEN p1.person_name END SEPARATOR ', ') AS directors,GROUP_CONCAT(DISTINCT CASE WHEN r1.role_type = 'actor' THEN p1.person_name END SEPARATOR ', ') AS actors FROM movie m left JOIN role r1 ON r1.movie_id = m.movie_id left JOIN person p1 ON r1.person_id = p1.person_id where m.movie_id=%s GROUP BY m.movie_id, m.movie_title;"
    cursor.execute(query, (code,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result

def get_critics_by_code(code):
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "select member.member_name,rate.rate_stars from rate join member on member.member_id=rate.member_id where movie_id=%s"
    cursor.execute(query, (code,))
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result

@app.route('/title/<int:movie_id>/')
def movie_detail(movie_id):
    movie = get_movie_by_code(movie_id)  # 查詢 movie_id
    critics = get_critics_by_code(movie_id)
    if movie:
        return render_template('movie.html', movie=movie, critics=critics)
    else:
        return "這個電影的資訊迷失在宇宙盡頭……", 404
    
@app.route('/title/staff/')
def staff_page():
    keyword = request.args.get('find_data')  # 取得搜尋字串

if __name__ == '__main__':
    try:
        connect=pool.get_connection()
        cursor=connect.cursor()
        cursor.execute("SHOW TABLES;")
        print("CONNECTED, Tables:")
        for (table_name,) in cursor:
            print(" -",table_name)
        cursor.close()
        connect.close()
    except:
        print("...0^0...")
        
    app.run(debug=True)