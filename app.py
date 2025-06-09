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
    grade_field = request.args.get('grade_field')
    front_year = request.args.get('front_year')
    last_year = request.args.get('last_year')
    query = "SELECT distinct movie.movie_id,movie.movie_title FROM movie"
    
    if(field=="title"):
        query += f" WHERE movie_title LIKE %s"
    else:
        query += f" inner join role on role.movie_id=movie.movie_id inner join person on role.person_id=person.person_id WHERE person.person_name LIKE %s AND role.role_type IN ('{field}')"
    if(grade_field!="--"):
        query += f" and movie.movie_grade in ('{grade_field}')"
    if(front_year!=""):
        query += f" and YEAR(movie.movie_release) >= {front_year}"
    if(last_year!=""):
        query += f" and YEAR(movie.movie_release) <= {last_year}"
    like_pattern = f"%{keyword}%"  # 模糊搜尋，含有關鍵字
    cursor.execute(query, (like_pattern,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

@app.route('/search')
def search():
    keyword = request.args.get('find')  # 取得搜尋字串
    results = search_movies(keyword)  # 從資料庫查詢
    print(results)
    return render_template('search.html', results=results,count=len(results))  # 把結果丟回 main.html

def get_movie_by_code(code):
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT m.*,GROUP_CONCAT(DISTINCT CASE WHEN r1.role_type = 'director' THEN p1.person_name END SEPARATOR ', ') AS directors,GROUP_CONCAT(DISTINCT CASE WHEN r1.role_type = 'actor' or r1.role_type = 'actress' THEN p1.person_name END SEPARATOR ', ') AS actors FROM movie m left JOIN role r1 ON r1.movie_id = m.movie_id left JOIN person p1 ON r1.person_id = p1.person_id where m.movie_id=%s GROUP BY m.movie_id, m.movie_title;"
    cursor.execute(query, (code,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result

def get_critics_by_code(code):
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "select member.member_name,rate.rate_stars,rate.rate_critics from rate join member on member.member_id=rate.member_id where movie_id=%s"
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
    
@app.route('/staff')
def staff_page():
    return render_template('staff.html')

@app.route('/staff/movie', methods=['GET']) # 不過預設就是GET所以加不加都沒差
def staff_page_movie():
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM movie")
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('staff_edit.html', movies=movies)
@app.route('/staff/movie/add', methods=['POST'])
def add_movie():
    title = request.form['title']
    release_year = request.form['release_year']
    charge = request.form['charge']
    length = request.form['length']
    genre = request.form['genre']
    grade = request.form['grade']
    picture = request.form['picture']
    desc = request.form['describe']
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movie")
    idnum = cursor.fetchone()[0]+1
    cursor.execute("INSERT INTO movie (movie_id, movie_title, movie_release, movie_charge, movie_length, movie_genre, movie_grade, movie_picture, movie_describe) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                   (idnum, title, release_year, charge, length, genre, grade, picture, desc))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/staff/movie')

@app.route('/staff/movie/update/<int:movie_id>', methods=['POST'])
def update_movie(movie_id):
    title = request.form['title']
    release_year = request.form['release_year']
    charge = request.form['charge']
    length = request.form['length']
    genre = request.form['genre']
    grade = request.form['grade']
    picture = request.form['picture']
    desc = request.form['describe']
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE movie SET movie_title=%s, movie_release=%s, movie_charge=%s, movie_length=%s, movie_genre=%s, movie_grade=%s, movie_picture=%s, movie_describe=%s WHERE movie_id=%s",
                   (title, release_year, charge, length, genre, grade, picture, desc, movie_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/staff/movie')

@app.route('/staff/movie/delete/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movie WHERE movie_id=%s", (movie_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/staff/movie')

@app.route('/staff/member', methods=['GET'])
def staff_page_member():
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM member")
    member = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('staff_mem.html', member=member)

@app.route('/staff/member/add', methods=['POST'])
def add_member():
    member_name = request.form['member_name']
    email = request.form['email']
    character = request.form['character']
    status = "inactive"
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM member")
    idnum = cursor.fetchone()[0]+1
    cursor.execute("INSERT INTO member (member_id, member_name, member_email, member_character, member_status) VALUES (%s, %s, %s, %s, %s)",
                   (idnum, member_name, email, character, status))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/staff/member')

@app.route('/staff/member/update/<int:member_id>', methods=['POST'])
def update_member(member_id):
    member_name = request.form['member_name']
    email = request.form['email']
    character = request.form['character']
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE member SET member_name=%s, member_email=%s, member_character=%s WHERE member_id=%s",
                   (member_name, email, character, member_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/staff/member')

@app.route('/staff/member/delete/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM member WHERE member_id=%s", (member_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/staff/member')

@app.route('/staff/member/<int:member_id>/transactions')
def view_transactions(member_id):
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "select member.member_name from member where member.member_id=%s"
    cursor.execute(query, (member_id,))
    member_name = cursor.fetchone()

    query = """
        SELECT dl.download_date, m.movie_title,
               p.payment_amount, p.payment_date
        FROM download_library dl
        JOIN movie m ON dl.movie_id = m.movie_id
        LEFT JOIN payment p ON dl.member_id = p.member_id AND dl.movie_id = p.movie_id
        WHERE dl.member_id = %s
        ORDER BY dl.download_date DESC
    """
    cursor.execute(query, (member_id,))
    transactions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('staff_mem_transactions.html', transactions=transactions, member_name=member_name)

@app.route('/staff/search')
def staff_page_search():
    return render_template('staff_search.html')

@app.route('/staff/search/filter')
def dynamic_search():
    genre = request.args.get('genre')
    target = request.args.get('target')
    condition = request.args.get('condition')
    order = request.args.get('order', 'desc') # 如果沒有傳入 order 參數，則預設用 "desc"
    front_year = request.args.get('front_year')
    last_year = request.args.get('last_year')
    limit = int(request.args.get('limit', 10))
    
    if not genre:
        genre="%"
    if not front_year:
        front_year="1900/01"
    if not last_year:
        last_year="2100/01"

    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 動態 SQL 組合邏輯
    if target == 'movie':
        if condition == 'downloads':
            query = f"""
                SELECT m.movie_title AS name, COUNT(*) AS value
                FROM download_library d
                JOIN movie m ON d.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(d.download_date) >= {front_year}
                and YEAR(d.download_date) <= {last_year}
                GROUP BY d.movie_id
                ORDER BY value {order} LIMIT %s
            """
        elif condition == 'revenue':
            query = f"""
                SELECT m.movie_title AS name, SUM(p.payment_amount) AS value
                FROM payment p
                JOIN movie m ON p.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(p.payment_date) >= {front_year}
                and YEAR(p.payment_date) <= {last_year}
                GROUP BY p.movie_id
                ORDER BY value {order} LIMIT %s
            """

    elif target == 'member':
        if condition == 'downloads':
            query = f"""
                SELECT mem.member_name AS name, COUNT(*) AS value
                FROM download_library d
                JOIN member mem ON d.member_id = mem.member_id
                JOIN movie m ON d.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(d.download_date) >= {front_year}
                and YEAR(d.download_date) <= {last_year}
                GROUP BY d.member_id
                ORDER BY value {order} LIMIT %s
            """
        elif condition == 'revenue':
            query = f"""
                SELECT mem.member_name AS name, SUM(p.payment_amount) AS value
                FROM payment p
                JOIN member mem ON p.member_id = mem.member_id
                JOIN movie m ON p.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(p.payment_date) >= {front_year}
                and YEAR(p.payment_date) <= {last_year}
                GROUP BY p.member_id
                ORDER BY value {order} LIMIT %s
            """

    elif target == 'genre':
        if condition == 'downloads':
             query = f"""
                SELECT m.movie_genre AS name, COUNT(*) AS value
                FROM download_library d
                JOIN movie m ON d.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(d.download_date) >= {front_year}
                and YEAR(d.download_date) <= {last_year}
                GROUP BY m.movie_genre
                ORDER BY value {order} LIMIT %s
            """
        elif condition == 'revenue':
            query = f"""
                SELECT m.movie_genre AS name, SUM(p.payment_amount) AS value
                FROM payment p
                JOIN movie m ON p.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(p.payment_date) >= {front_year}
                and YEAR(p.payment_date) <= {last_year}
                GROUP BY m.movie_genre
                ORDER BY value {order} LIMIT %s
            """

    elif target == 'month':
        if condition == 'downloads':
            query = f"""
                SELECT DATE_FORMAT(d.download_date, '%Y-%m') AS name, COUNT(*) AS value
                FROM download_library d
                JOIN movie m ON d.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(d.download_date) >= {front_year}
                and YEAR(d.download_date) <= {last_year}
                GROUP BY name
                ORDER BY value {order} LIMIT %s
            """
        elif condition == 'revenue':
            query = f"""
                SELECT DATE_FORMAT(p.payment_date, '%Y-%m') AS name, SUM(p.payment_amount) AS value
                FROM payment p
                JOIN movie m ON p.movie_id = m.movie_id
                where m.movie_genre like %s
                and YEAR(p.payment_date) >= {front_year}
                and YEAR(p.payment_date) <= {last_year}
                GROUP BY name
                ORDER BY value {order} LIMIT %s
            """

    else:
        query = "SELECT '無效查詢' AS name, 0 AS value"

    cursor.execute(query, (genre, limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('staff_search.html', result=result)

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