from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import mysql.connector
import bcrypt
import os
import re
from datetime import datetime, timedelta, time,date
from flask import render_template
import logging
import serial 


import logging
logging.basicConfig(level=logging.DEBUG)





app = Flask(__name__)
CORS(app)

# 設定 JWT
app.config["JWT_SECRET_KEY"] = os.getenv("STUDENT_JWT_SECRET", "student_secret_key")  
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5)

jwt = JWTManager(app)

# 資料庫配置
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Aa0901155900",  # 替換為你的資料庫密碼
    "database": "studentif"  # 替換為你的資料庫名稱
}

@app.errorhandler(422)
def handle_unprocessable_entity(e):
    return jsonify({"message": "Unprocessable Entity", "error": str(e)}), 422

# 登入 API
@app.route('/api/t_login', methods=['POST'])
def teacher_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "請輸入帳號與密碼"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查詢教師帳號
        query = "SELECT password FROM t_account WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result and bcrypt.checkpw(password.encode('utf-8'), result['password'].encode('utf-8')):
            # 生成 Token
            token = create_access_token(identity=username)
            return jsonify({"access_token": token}), 200
        else:
            return jsonify({"message": "帳號或密碼錯誤"}), 401

    except Exception as e:
        return jsonify({"message": f"發生錯誤：{str(e)}"}), 500

    finally:
        cursor.close()
        connection.close()


# 🔹 教師驗證 API (確認 Token 是否有效)
@app.route('/api/teacher/verify', methods=['GET'])
@jwt_required()
def verify_teacher():
    current_user = get_jwt_identity()
    return jsonify({"message": "教師驗證成功", "username": current_user}), 200

@app.route('/api/get-max-students', methods=['GET'])
def get_max_students():
    class_code = request.args.get('classId')  # 這裡可能是 classId 或 class_code

    if not class_code:
        return jsonify({"message": "缺少 classId 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT max_students FROM classes WHERE class_code = %s"
        cursor.execute(query, (class_code,))
        result = cursor.fetchone()

        if result:
            return jsonify({"max_students": result["max_students"]}), 200
        else:
            return jsonify({"message": "查無此班級"}), 404

    except Exception as e:
        return jsonify({"message": f"發生錯誤: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
@app.route('/test/<classId>', methods=['GET', 'POST', 'DELETE'])
def test():
    if request.method == 'GET':
        print("收到 GET 測試請求")
        return jsonify({"status": "success", "message": "GET 測試 API 正常運作"}), 200

    elif request.method == 'POST':
        data = request.get_json()
        print(f"收到 POST 測試資料：{data}")
        return jsonify({"status": "success", "message": "已收到 POST 測試資料", "data": data}), 200

    elif request.method == 'DELETE':
        print("收到 DELETE 測試請求")
        return jsonify({"status": "success", "message": "DELETE 測試 API 正常運作"}), 200


@app.route('/delete_class', methods=['DELETE'])
def delete_class():
    conn = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        class_id = data.get("class_id")
        if not class_id:
            return jsonify({"status": "error", "message": "未提供 class_id"}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 這行會執行 SQL，預設 autocommit=False 時，交易已經開始了
        cursor.execute("SELECT 1 FROM classes WHERE class_code = %s", (class_id,))
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": f"查無此班級 {class_id}"}), 404

        # ❌ 不要再呼叫 conn.start_transaction() 了
        # conn.start_transaction()

        # 刪附屬資料表
        cursor.execute(f"DROP TABLE IF EXISTS `class_{class_id}_students`")
        cursor.execute(f"DROP TABLE IF EXISTS `{class_id}_attendance`")
        cursor.execute(f"DROP TABLE IF EXISTS `class_{class_id}_grades`")

        # 刪班表、課表
        cursor.execute("DELETE FROM class_schedule WHERE class_code = %s", (class_id,))
        cursor.execute("DELETE FROM classes WHERE class_code = %s", (class_id,))

        # 向左緊縮 account 的 class1/2/3（若不允許 NULL，改成 ''）
        cursor.execute("""
            UPDATE account
            SET class1 = class2,
                class2 = class3,
                class3 = NULL
            WHERE class1 = %s
        """, (class_id,))
        moved_from_c1 = cursor.rowcount

        cursor.execute("""
            UPDATE account
            SET class2 = class3,
                class3 = NULL
            WHERE class2 = %s
        """, (class_id,))
        moved_from_c2 = cursor.rowcount

        cursor.execute("""
            UPDATE account
            SET class3 = NULL
            WHERE class3 = %s
        """, (class_id,))
        cleared_c3 = cursor.rowcount

        conn.commit()
        return jsonify({
            "status": "success",
            "message": f"班級 {class_id} 已刪除，並完成 account 欄位向左移動。",
            "account_updates": {
                "moved_from_class1": moved_from_c1,
                "moved_from_class2": moved_from_c2,
                "cleared_class3": cleared_c3
            }
        }), 200

    except mysql.connector.Error as e:
        if conn: conn.rollback()
        return jsonify({"status": "error", "message": f"資料庫錯誤: {str(e)}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"status": "error", "message": f"伺服器錯誤: {str(e)}"}), 500
    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
            
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    card_num = data.get("card_num")

    # 驗證所有欄位是否填寫
    missing_fields = [field for field, value in {
        "username": username,
        "password": password,
        "name": name,
        "email": email,
        "phone": phone,
        "card_num": card_num
    }.items() if not value]

    if missing_fields:
        return jsonify({"message": f"以下欄位未填寫：{', '.join(missing_fields)}"}), 400

    # 驗證帳號長度
    if len(username) < 5:
        return jsonify({"message": "帳號必須至少 5 個字以上！"}), 400

    # 驗證密碼格式
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    if not re.match(password_regex, password):
        return jsonify({"message": "密碼必須至少 8 個字以上，包含大小寫字母和數字！"}), 400

    # 驗證電子郵件格式
    email_regex = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    if not re.match(email_regex, email):
        return jsonify({"message": "請輸入正確的 Gmail 地址！"}), 400

    # 驗證電話號碼格式
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({"message": "請輸入正確的電話號碼！"}), 400

    try:
        # 連接到資料庫
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 檢查重複資料
        cursor.execute("SELECT id FROM account WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"message": "該帳號名稱已被使用，請更換！"}), 400

        cursor.execute("SELECT id FROM account WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "該電子郵件已被使用，請更換！"}), 400

        cursor.execute("SELECT id FROM account WHERE phone = %s", (phone,))
        if cursor.fetchone():
            return jsonify({"message": "該電話號碼已被使用，請更換！"}), 400

        cursor.execute("SELECT id FROM account WHERE card_num = %s", (card_num,))
        if cursor.fetchone():
            return jsonify({"message": "此卡號已被註冊，請使用另一張卡片"}), 400

        # 插入資料
        insert_query = """
            INSERT INTO account (username, password, name, email, phone, card_num)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (username, password, name, email, phone, card_num))
        connection.commit()

        return jsonify({"message": "帳號創建成功"}), 201

    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        return jsonify({"message": "帳號創建失敗"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



def create_class_students_table(cursor, class_code):
    """
    根據班級代碼創建學生表
    """
    table_name = f"class_{class_code}_students"

    create_table_query = f"""
    CREATE TABLE {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id VARCHAR(20) NOT NULL UNIQUE,
        student_name VARCHAR(100) NOT NULL,
        student_email VARCHAR(100) NOT NULL,
        student_phone VARCHAR(15),
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_query)

def create_attendance_table(cursor, class_code, start_date, class_count):
    """
    創建點名表，基於開課日期和課程堂數。
    """
    try:
        # 確保 class_count 是整數
        class_count = int(class_count)

        # 將 start_date 轉換為日期類型
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(class_count):
            # 計算每堂課的日期
            current_date = (start_date_obj + timedelta(days=i * 7)).strftime("%Y_%m_%d")

            # 動態生成列名
            attendance_column = f"`attendance_{current_date}` ENUM('出席', '遲到', '缺席') DEFAULT '缺席'"
            time_column = f"`time_{current_date}` TIME"

            # 創建表格（如果尚未存在）
            query_create = f"""
            CREATE TABLE IF NOT EXISTS `{class_code}_attendance` (
                student_id INT NOT NULL,
                {attendance_column},
                {time_column},
                PRIMARY KEY (student_id, {attendance_column.split(' ')[0]})
            )
            """
            cursor.execute(query_create)

    except ValueError:
        raise ValueError("class_count 必須是可轉換為整數的值！")


   
@app.route('/api/get-classes', methods=['GET'])
def get_classes():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT class_code AS id, class_name AS name, teacher_name AS teacher, students_count AS students FROM classes"
        cursor.execute(query)
        classes = cursor.fetchall()

        return jsonify(classes), 200

    except mysql.connector.Error as err:
        return jsonify({"message": f"資料庫錯誤: {err}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
@app.route('/api/get-class-info', methods=['GET'])
def get_class_info():
    # 獲取前端傳遞的 classId
    class_id = request.args.get('classId')

    if not class_id:
        return jsonify({"error": "缺少 classId 參數"}), 400

    try:
        # 建立資料庫連線
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查詢班級資訊
        query = """
        SELECT * FROM classes WHERE class_code = %s
        """
        cursor.execute(query, (class_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "班級不存在"}), 404

        # 返回班級資訊
        return jsonify({
            "class_name": result['class_name'],
            "teacher_name": result['teacher_name'],
            "start_date": result['start_date'],
            "end_date": result['end_date'],
            "students_count": result['students_count'],
            "max_students": result['max_students']
        })

    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

    finally:
        # 關閉連線
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
@app.route('/api/students', methods=['GET'])
def api_students():
    try:
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM account")
        students = cursor.fetchall()
        return jsonify({"status": "success", "data": students})
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/get-students', methods=['GET'])
def get_students():
    class_code = request.args.get('classId')
    if not class_code:
        return jsonify({"message": "班級代碼缺失"}), 400

    table_name = f"class_{class_code}_students"

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM `{table_name}`"
        cursor.execute(query)
        students = cursor.fetchall()

        if not students:
            return jsonify({"message": "目前無學生", "students": []})

        return jsonify({"students": students})
    except mysql.connector.Error as err:
        return jsonify({"message": f"資料庫錯誤: {err}"}), 500
    except Exception as e:
        return jsonify({"message": f"伺服器錯誤: {str(e)}"}), 500

@app.route('/api/get-class-students', methods=['GET'])
def get_class_students():
    class_code = request.args.get('class_code')

    if not class_code:
        return jsonify({"error": "缺少 class_code 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查詢班級學生表，獲取學生學號
        query = f"SELECT student_id, student_name, student_email, student_phone FROM class_{class_code}_students"
        cursor.execute(query)
        students = cursor.fetchall()
        for student in students:
            student["name"] = student.pop("student_name")
            student["email"] = student.pop("student_email")
            student["phone"] = student.pop("student_phone")
        return jsonify(students), 200

    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/get-non-class-students', methods=['GET'])
def get_non_class_students():
    class_code = request.args.get('class_code')

    if not class_code:
        return jsonify({"error": "缺少 class_code 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 1️⃣ 先獲取班級內的學生 ID
        query_get_class_students = f"SELECT student_id FROM class_{class_code}_students"
        cursor.execute(query_get_class_students)
        class_students = cursor.fetchall()
        class_student_ids = {student["student_id"] for student in class_students}  # 轉成 Set

        # 2️⃣ 查詢 `account` 表，排除班級內的學生
        query_get_all_students = "SELECT username AS student_id, name, email, phone FROM account"
        cursor.execute(query_get_all_students)
        all_students = cursor.fetchall()

        # 3️⃣ 過濾掉已經在班級內的學生
        non_class_students = [student for student in all_students if student["student_id"] not in class_student_ids]

        return jsonify(non_class_students), 200

    except Exception as e:
        return jsonify({"error": f"發生錯誤：{str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route('/api/update-class-students', methods=['POST'])
def update_class_students():
    data = request.json
    class_code = data.get('classCode')
    added_students = data.get('addedStudents', [])
    removed_students = data.get('removedStudents', [])

    if not class_code:
        return jsonify({"error": "缺少 class_code 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # **1️⃣ 處理新增的學生**
        for student in added_students:
            student_id = student['student_id']

            # 先查 account 表，看看 class1 ~ class3 狀況
            cursor.execute("SELECT class1, class2, class3 FROM account WHERE username = %s", (student_id,))
            account_info = cursor.fetchone()

            if not account_info:
                return jsonify({"message": f"學生 {student_id} 不存在"}), 400

            class1, class2, class3 = account_info["class1"], account_info["class2"], account_info["class3"]

            # 檢查是否已經選過這個班
            if class_code in [class1, class2, class3]:
                continue  # 已存在就跳過

            # 決定放到哪個欄位
            if not class1:
                cursor.execute("UPDATE account SET class1 = %s WHERE username = %s", (class_code, student_id))
            elif not class2:
                cursor.execute("UPDATE account SET class2 = %s WHERE username = %s", (class_code, student_id))
            elif not class3:
                cursor.execute("UPDATE account SET class3 = %s WHERE username = %s", (class_code, student_id))
            else:
                return jsonify({"message": f"學生 {student_id} 已經有三個班級，無法再加入"}), 400

            # 新增到 class_{class_code}_students
            cursor.execute(f"SELECT * FROM class_{class_code}_students WHERE student_id = %s", (student_id,))
            result = cursor.fetchone()
            if not result:
                insert_student_query = f"""
                INSERT INTO class_{class_code}_students (student_id, student_name, student_email, student_phone)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_student_query, (student_id, student['name'], student['email'], student['phone']))

            # 新增到 {class_code}_attendance
            cursor.execute(f"SELECT * FROM {class_code}_attendance WHERE student_id = %s", (student_id,))
            attendance_result = cursor.fetchone()
            if not attendance_result:
                cursor.execute(f"INSERT INTO {class_code}_attendance (student_id) VALUES (%s)", (student_id,))

        # **2️⃣ 處理刪除的學生**
        for student in removed_students:
            student_id = student['student_id']

            # 先刪掉班級學生表 & 點名表
            cursor.execute(f"DELETE FROM class_{class_code}_students WHERE student_id = %s", (student_id,))
            cursor.execute(f"DELETE FROM {class_code}_attendance WHERE student_id = %s", (student_id,))

            # 更新 account 的 class1~class3 欄位
            cursor.execute("SELECT class1, class2, class3 FROM account WHERE username = %s", (student_id,))
            account_info = cursor.fetchone()

            if account_info:
                class1, class2, class3 = account_info["class1"], account_info["class2"], account_info["class3"]
                classes = [class1, class2, class3]

                # 把這個 class_code 移除
                new_classes = [c for c in classes if c != class_code]

                # 把空格往前移（例如 [C001, None, C002] → [C001, C002, None]）
                while len(new_classes) < 3:
                    new_classes.append(None)

                cursor.execute(
                    "UPDATE account SET class1 = %s, class2 = %s, class3 = %s WHERE username = %s",
                    (new_classes[0], new_classes[1], new_classes[2], student_id)
                )

        # **3️⃣ 更新班級學生數**
        update_count_query = f"""
        UPDATE classes
        SET students_count = (SELECT COUNT(*) FROM class_{class_code}_students)
        WHERE class_code = %s
        """
        cursor.execute(update_count_query, (class_code,))

        connection.commit()
        return jsonify({"message": "班級學生資料更新成功！"}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"message": f"發生錯誤：{str(e)}"}), 500

    finally:
        if cursor: cursor.close()
        if connection: connection.close()


# 🔹 定義一週的日期對應
WEEKDAYS = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}
@app.route('/api/active_classes', methods=['GET'])
def get_active_classes():
    now = datetime.now()
    current_day = now.strftime("%A")               # e.g. 'Thursday'
    current_time = now.strftime("%H:%M:%S")        # e.g. '18:20:00'

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT * FROM class_schedule
            WHERE class_day = %s AND start_time <= %s AND end_time >= %s
        """
        cursor.execute(query, (current_day, current_time, current_time))
        results = cursor.fetchall()

        # ✅ 將 TIME or TIMESTAMP 欄位轉成字串，避免 jsonify 錯誤
        for row in results:
            for field in ['start_time', 'end_time']:
                val = row.get(field)
                if isinstance(val, (time, timedelta)):
                    row[field] = str(val)

        return jsonify({"status": "success", "classes": results})

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500

    finally:
        cursor.close()
        conn.close()




@app.route('/api/create-class', methods=['POST'])
def create_class():
    data = request.json

    class_code = data.get("class_code")
    class_name = data.get("class_name")
    teacher_name = data.get("teacher_name")
    max_students = data.get("max_students")
    class_count = data.get("class_count")
    start_date = data.get("start_date")
    schedule = data.get("schedule")  # 包含 { day, start_time, end_time }

    if not (class_code and class_name and teacher_name and max_students and class_count and start_date and schedule):
        return jsonify({"message": "缺少必要的參數"}), 400

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # **計算 end_date**
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = start_date_obj + timedelta(weeks=int(class_count))
        end_date = end_date_obj.strftime("%Y-%m-%d")

        # **1️⃣ 新增班級到 `classes` 資料表**
        insert_class_query = """
            INSERT INTO classes (class_code, class_name, teacher_name, max_students, class_count, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_class_query, (class_code, class_name, teacher_name, max_students, class_count, start_date, end_date))

        # **2️⃣ 新增課程時間表到 `class_schedule`**
        for entry in schedule:
            class_day = entry.get("day")
            start_time = entry.get("start_time", "00:00:00")
            end_time = entry.get("end_time", "00:00:00")

            if not class_day:
                return jsonify({"message": "缺少 class_day"}), 400

            insert_schedule_query = """
                INSERT INTO class_schedule (class_code, class_day, start_time, end_time)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_schedule_query, (class_code, class_day, start_time, end_time))

        # **3️⃣ 創建該班級的學生表 (`class_{class_code}_students`)**
        create_students_table_query = f"""
            CREATE TABLE IF NOT EXISTS `class_{class_code}_students` (
                student_id VARCHAR(255) NOT NULL,
                student_name VARCHAR(255),
                student_email VARCHAR(255),
                student_phone VARCHAR(20),
                PRIMARY KEY (student_id)
            )
        """
        cursor.execute(create_students_table_query)

        # **4️⃣ 建立點名表 (`{class_code}_attendance`)**
        attendance_columns = []
        for i in range(int(class_count)):
            class_date = (start_date_obj + timedelta(days=i * 7)).strftime("%Y_%m_%d")
            attendance_columns.append(f"`attendance_{class_date}` ENUM('出席', '遲到', '缺席') DEFAULT '缺席'")
            attendance_columns.append(f"`time_{class_date}` TIME")

        create_attendance_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{class_code}_attendance` (
                student_id VARCHAR(255) NOT NULL,
                {', '.join(attendance_columns)},
                PRIMARY KEY (student_id)
            )
        """
        # 5.建立成績表
        cursor.execute(create_attendance_table_query)
        create_grades_table_query = f"""
            CREATE TABLE IF NOT EXISTS `class_{class_code}_grades` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(255) NOT NULL,
                student_name VARCHAR(255),
                exam_name VARCHAR(255) NOT NULL,
                score FLOAT DEFAULT 0
            )
        """
        cursor.execute(create_grades_table_query)


        connection.commit()
        return jsonify({"message": "班級創建成功！"}), 201

    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        return jsonify({"message": f"資料庫錯誤：{str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
@app.route('/api/grade-get-students', methods=['GET'])
def grade_get_students():
    class_code = request.args.get("classId")
    if not class_code:
        return jsonify({"message": "缺少 classId"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        table_name = f"class_{class_code}_students"
        query = f"SELECT student_id, student_name FROM `{table_name}`"
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify({"students": results}), 200
    except mysql.connector.Error as e:
        return jsonify({"message": f"資料庫錯誤: {str(e)}"}), 500
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

# 5️⃣ 新增小考（批量新增成績）
@app.route('/api/add-exam', methods=['POST'])
def add_exam():
    data = request.json
    class_code = data.get("classId")
    exam_name = data.get("exam_name")
    grades = data.get("grades")

    if not (class_code and exam_name and grades):
        return jsonify({"message": "缺少必要參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        table_name = f"class_{class_code}_grades"
        query = f"INSERT INTO `{table_name}` (student_id, student_name, exam_name, score) VALUES (%s, %s, %s, %s)"

        for g in grades:
            cursor.execute(query, (g["student_id"], g["student_name"], exam_name, g["score"]))

        connection.commit()
        return jsonify({"message": f"小考 {exam_name} 新增成功"}), 200
    except mysql.connector.Error as e:
        return jsonify({"message": f"資料庫錯誤: {str(e)}"}), 500
    finally:
        if cursor: cursor.close()
        if connection: connection.close()            
            
@app.route('/api/update-grade', methods=['POST'])
def update_grade():
    data = request.json
    class_code = data.get("classId")
    student_id = data.get("student_id")
    exam_name = data.get("exam_name")
    score = data.get("score")

    if not (class_code and student_id and exam_name and score is not None):
        return jsonify({"message": "缺少必要參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        table_name = f"class_{class_code}_grades"
        update_query = f"""
            UPDATE `{table_name}`
            SET score = %s
            WHERE student_id = %s AND exam_name = %s
        """
        cursor.execute(update_query, (score, student_id, exam_name))
        connection.commit()

        return jsonify({"message": "成績更新成功"}), 200

    except mysql.connector.Error as e:
        return jsonify({"message": f"資料庫錯誤: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
            
@app.route('/api/get-exams', methods=['GET'])
def get_exams():
    class_code = request.args.get("classId")

    if not class_code:
        return jsonify({"message": "缺少 classId"}), 400

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        table_name = f"class_{class_code}_grades"
        query = f"SELECT DISTINCT exam_name FROM `{table_name}` ORDER BY exam_name"
        cursor.execute(query)
        results = [row[0] for row in cursor.fetchall()]

        return jsonify({"exams": results}), 200

    except mysql.connector.Error as e:
        return jsonify({"message": f"資料庫錯誤: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
@app.route('/api/get-exam-grades', methods=['GET'])
def get_exam_grades():
    class_code = request.args.get("classId")
    exam_name = request.args.get("exam")

    if not class_code or not exam_name:
        return jsonify({"message": "缺少 classId 或 exam"}), 400

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        table_name = f"class_{class_code}_grades"
        query = f"""
            SELECT student_id, student_name, score
            FROM `{table_name}`
            WHERE exam_name = %s
        """
        cursor.execute(query, (exam_name,))
        results = cursor.fetchall()

        return jsonify({"grades": results}), 200

    except mysql.connector.Error as e:
        return jsonify({"message": f"資料庫錯誤: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
# ✅ 手動輸入學號點名
@app.route('/attendance/manual', methods=['POST'])
def manual_attendance():
    data = request.get_json()
    student_id = data.get('student_id')

    if not student_id:
        return jsonify({"status": "error", "message": "請提供學生學號"}), 400

    # 取得當下時間與星期幾
    now = datetime.now()
    current_day = now.strftime('%A')  # e.g., 'Friday'
    current_time = now.strftime('%H:%M:%S')
    today_str = now.strftime('%Y_%m_%d')  # 資料表的欄位格式

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查找目前上課中的班級
        query = """
        SELECT class_code FROM class_schedule 
        WHERE class_day = %s AND start_time <= %s AND end_time >= %s
        """
        cursor.execute(query, (current_day, current_time, current_time))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "目前無進行中課程"}), 400

        class_code = result['class_code']
        attendance_table = f"{class_code}_attendance"
        attendance_col = f"attendance_{today_str}"

        # 檢查欄位是否存在（只做一次初始化也可略過）
        cursor.execute(f"SHOW COLUMNS FROM {attendance_table} LIKE %s", (attendance_col,))
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": f"點名欄位 {attendance_col} 不存在"}), 500

        # 更新該學生今日出席狀態
        update_query = f"""
        UPDATE {attendance_table}
        SET {attendance_col} = '出席'
        WHERE student_id = %s
        """
        cursor.execute(update_query, (student_id,))
        connection.commit()

        return jsonify({"status": "success", "message": f"✅ {student_id} 已成功簽到"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"伺服器錯誤：{str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# ✅ 假設你有串接刷卡裝置，模擬回傳卡號對應的學生學號
@app.route('/attendance/card', methods=['GET'])
def card_attendance():
    try:
        # ✅ 從 COM13 讀取卡號
        ser = serial.Serial('COM13', 115200, timeout=3)
        card_num = ser.readline().decode().strip()
        ser.close()

        if not card_num:
            return jsonify({"status": "error", "message": "未讀到卡號"})

        # ✅ 查詢 account 資料表獲取 student_id
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username AS student_id FROM account WHERE card_num = %s", (card_num,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "查無此卡號"})

        student_id = result["student_id"]

        # ✅ 查目前正在上課的班級（含上課前15分鐘）
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime('%A')  # e.g., 'Friday'
        today_str = now.strftime('%Y_%m_%d')  # 用來組欄位名
        time_col = f"time_{today_str}"
        attendance_col = f"attendance_{today_str}"

        # ✅ 查找 class_schedule 中有符合條件的班級
        cursor.execute("""
            SELECT class_code 
            FROM class_schedule 
            WHERE class_day = %s 
              AND TIME(start_time) <= %s 
              AND TIME(end_time) >= %s
        """, (current_day, (datetime.combine(date.today(), current_time) + timedelta(minutes=15)).time(), current_time))
        
        classes = cursor.fetchall()

        if not classes:
            return jsonify({"status": "error", "message": "目前無課程可簽到"})

        updated_classes = []

        for row in classes:
            class_code = row["class_code"]
            table_name = f"{class_code}_attendance"

            # ✅ 檢查該表格是否有對應欄位，若無則新增欄位
            cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (attendance_col,))
            if cursor.fetchone() is None:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {attendance_col} VARCHAR(10)")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {time_col} TIME")

            # ✅ 寫入出席紀錄
            cursor.execute(
                f"UPDATE {table_name} SET {attendance_col} = '出席', {time_col} = %s WHERE student_id = %s",
                (current_time, student_id)
            )

            if cursor.rowcount > 0:
                updated_classes.append(class_code)

        conn.commit()

        if updated_classes:
            return jsonify({
                "status": "success",
                "card_num": card_num,
                "message": f"簽到成功：{', '.join(updated_classes)}",
                "student_id": student_id
            })
        else:
            return jsonify({
                "status": "error",
                "message": "未找到對應學生資料，或學生不在任何上課中的班級名單內"
            })

    except serial.SerialException:
        return jsonify({"status": "error", "message": "❌ 無法開啟 COM13，請檢查設備"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": f"❌ 錯誤：{str(e)}"}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

# ✅ 顯示今日所有學生簽到狀況
@app.route('/api/students_attendance_today', methods=['GET'])
def students_attendance_today():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 取出帳號資料
        cursor.execute("SELECT username AS student_id, name FROM account")
        students = cursor.fetchall()

        today = date.today()

        # 查詢今日簽到資料（學生 ID + 時間）
        cursor.execute("SELECT student_id, sign_time FROM attendance WHERE sign_date = %s", (today,))
        records = cursor.fetchall()
        time_map = {row['student_id']: str(row['sign_time']) for row in records}

        # 合併是否簽到與時間
        for s in students:
            sid = s['student_id']
            s['checked_in'] = sid in time_map
            s['sign_time'] = time_map.get(sid, '')  # 若沒簽到就空字串

        return jsonify({"status": "success", "students": students})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        cursor.close()
        conn.close()
@app.route('/get_card_num', methods=['GET'])
def get_card_num():
    try:
        import serial
        ser = serial.Serial("COM13", 115200, timeout=2)
        card_num = ser.readline().decode(errors='ignore').strip()
        if card_num:
            return jsonify({"status": "success", "card_num": card_num})
        else:
            return jsonify({"status": "error", "message": "未讀取到卡號"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-attendance-classes', methods=['GET'])
def get_attendance_classes():
    now = datetime.now()
    now_time_str = now.strftime('%H:%M:%S')
    future_time_str = (now + timedelta(minutes=15)).strftime('%H:%M:%S')
    today_day = now.strftime('%A')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT * FROM class_schedule
            WHERE class_day = %s
              AND start_time <= %s
              AND end_time > %s
        """
        cursor.execute(query, (today_day, future_time_str, now_time_str))
        classes = cursor.fetchall()

        return jsonify(classes), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        
@app.route('/api/s_login', methods=['POST'])
def student_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "請輸入帳號與密碼"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查詢帳號
        query = "SELECT password FROM account WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        # ✅ 純文字比對 (目前資料庫是明碼)
        if result and password == result['password']:
            # 生成 Token
            token = create_access_token(identity=username)
            return jsonify({"access_token": token}), 200
        else:
            return jsonify({"message": "帳號或密碼錯誤"}), 401

    except Exception as e:
        return jsonify({"message": f"發生錯誤：{str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
            
@app.route('/')
def login_page():
    return render_template('student/login.html')

@app.route('/home')
def home_page():
    return render_template('student/home.html')

@app.route('/register')
def register_page():
    return render_template('student/register.html')

@app.route('/grade')
def grade_page():
    return render_template('student/grade.html')

@app.route('/change_password')
def change_password_page():
    return render_template('change_password.html')

@app.route('/attendance_recode')
def attendance_recode_page():
    return render_template('attendance.html')

@app.errorhandler(422)
def handle_unprocessable_entity(e):
    return jsonify({"message": "Unprocessable Entity", "error": str(e)}), 422

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector

# ✅ 取「我的班級列表」
@app.route('/api/my_classes', methods=['GET'])
@jwt_required(optional=True)
def my_classes():
    student_id = request.args.get('studentId') or get_jwt_identity()
    if not student_id:
        return jsonify([]), 200

    conn = None; cur = None
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        # 1) 取 class1~class3
        cur.execute("""
            SELECT class1, class2, class3
            FROM account
            WHERE username = %s
        """, (student_id,))
        row = cur.fetchone() or {}
        class_codes = [c.strip() for c in [row.get('class1'), row.get('class2'), row.get('class3')] if c and c.strip()]
        if not class_codes:
            return jsonify([]), 200

        # 2) 撈課程（不在 SQL 端格式化日期）
        placeholders = ",".join(["%s"] * len(class_codes))
        order_expr   = ",".join(["%s"] * len(class_codes))
        sql = f"""
            SELECT
                class_code,
                class_name,
                teacher_name,
                start_date,   -- DATE / DATETIME 原樣取回
                end_date
            FROM classes
            WHERE class_code IN ({placeholders})
            ORDER BY FIELD(class_code, {order_expr})
        """
        cur.execute(sql, tuple(class_codes) + tuple(class_codes))
        rows = cur.fetchall() or []

        # 3) 在 Python 端把日期轉成 'YYYY-MM-DD' 字串
        def to_ymd(d):
            # d 可能是 datetime.date 或 datetime.datetime 或 None
            try:
                return d.strftime('%Y-%m-%d') if d else None
            except Exception:
                # 若欄位是 VARCHAR('2025-09-02') 就原樣回傳
                return str(d) if d is not None else None

        for r in rows:
            r['start_date'] = to_ymd(r.get('start_date'))
            r['end_date']   = to_ymd(r.get('end_date'))

        # 4) 補漏掉的課碼
        found = {r["class_code"] for r in rows}
        for code in class_codes:
            if code not in found:
                rows.append({
                    "class_code": code,
                    "class_name": None,
                    "teacher_name": None,
                    "start_date": None,
                    "end_date": None
                })

        return jsonify(rows), 200

    except Exception as e:
        print('[my_classes] error:', e)
        return jsonify({"error": "server error"}), 500
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except: pass




# ✅ 取「某課成績」（以網址或 JWT 決定誰）
@app.route('/api/class_grade/<class_code>', methods=['GET'])
@jwt_required(optional=True)
def class_grade(class_code):
    student_id = request.args.get('studentId') or get_jwt_identity()
    print('[class_grade]', class_code, 'student_id =', student_id)

    if not student_id:
        return jsonify([]), 200

    conn = None; cur = None
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        # 安全：確認該生確實選了這門課（防越權）
        cur.execute("""
            SELECT 1
            FROM account
            WHERE username = %s AND (%s IN (class1, class2, class3))
        """, (student_id, class_code))
        if not cur.fetchone():
            return jsonify([]), 200

        table_name = f"class_{class_code}_grades"

        # 表存在性檢查
        cur.execute("""
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = %s
        """, (table_name,))
        if not cur.fetchone():
            return jsonify([]), 200

        # 查成績（你的欄位 exam_name, score）
        cur.execute(f"""
            SELECT exam_name, score
            FROM `{table_name}`
            WHERE student_id = %s
            ORDER BY id ASC
        """, (student_id,))
        grades = cur.fetchall()

        return jsonify(grades), 200

    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except:
            pass


@app.errorhandler(422)
def handle_unprocessable_entity(e):
    print("422 Error:", e)
    return jsonify({"message": "Unprocessable Entity", "error": str(e)}), 422

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector

@app.route('/api/change_password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json(silent=True) or {}
    old_password = (data.get('old_password') or '').strip()
    new_password = (data.get('new_password') or '').strip()
    username = get_jwt_identity()  # ✅ 用 JWT 身分，不信 query string

    if not old_password or not new_password:
        return jsonify({"message": "請填寫所有欄位"}), 400
    if old_password == new_password:
        return jsonify({"message": "新密碼不可與舊密碼相同"}), 400

    conn = None; cur = None
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT password FROM account WHERE username=%s", (username,))
        row = cur.fetchone()
        if not row:
            return jsonify({"message": "找不到使用者"}), 404

        stored = (row['password'] or '').strip()

        # ✅ 明碼比對
        if old_password != stored:
            return jsonify({"message": "舊密碼錯誤"}), 401

        # ✅ 明碼直接更新
        cur.execute("UPDATE account SET password=%s WHERE username=%s", (new_password, username))
        conn.commit()

        return jsonify({"message": "密碼修改成功！"}), 200

    except mysql.connector.Error as e:
        if conn: conn.rollback()
        return jsonify({"message": f"資料庫錯誤: {e}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"message": f"伺服器錯誤: {e}"}), 500
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except:
            pass


@app.route('/api/my_attendance', methods=['GET'])
@jwt_required(optional=True)
def my_attendance():
    # 1) 身分來源：先用網址 ?studentId=，沒有再用 JWT
    student_id = request.args.get('studentId') or get_jwt_identity()
    class_code_filter = request.args.get('classCode')  # 可選：只查單一課
    if not student_id:
        return jsonify([]), 200

    conn = None; cur = None
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)

        # 2) 要查哪些班：若有帶 classCode 就用它，否則從 account 取 class1~3
        class_codes = []
        if class_code_filter:
            class_codes = [class_code_filter.strip()]
        else:
            cur.execute("""
                SELECT class1, class2, class3
                FROM account
                WHERE username = %s
            """, (student_id,))
            row = cur.fetchone() or {}
            class_codes = [c.strip() for c in [row.get('class1'), row.get('class2'), row.get('class3')] if c and c.strip()]

        if not class_codes:
            return jsonify([]), 200

        # 3) 取課名
        placeholders = ",".join(["%s"] * len(class_codes))
        cur.execute(f"""
            SELECT class_code, class_name
            FROM classes
            WHERE class_code IN ({placeholders})
        """, tuple(class_codes))
        classes_map = {r["class_code"]: r["class_name"] for r in cur.fetchall()}

        records = []

        for code in class_codes:
            table_name = f"{code}_attendance"   # 你的表命名：c001_attendance

            # 表存在性檢查
            cur.execute("""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = %s
            """, (table_name,))
            if not cur.fetchone():
                continue

            # 撈這位學生的整列
            cur.execute(f"SELECT * FROM `{table_name}` WHERE student_id = %s", (student_id,))
            row = cur.fetchone()
            if not row:
                continue

            # 4) 欄轉列：掃描所有 attendance_YYYY_MM_DD 欄位
            for col, val in row.items():
                if not col.startswith("attendance_"):
                    continue
                date_token = col[len("attendance_"):]           # e.g. 2025_09_02
                status = val                                    # '出席' / '遲到' / '缺席' / None
                time_val = row.get(f"time_{date_token}")        # 可能是 None 或 time 物件

                # 只輸出有紀錄的（你也可以改成全丟出）
                if status is None:
                    continue

                # 組回傳格式
                records.append({
                    "class_code": code,
                    "class_name": classes_map.get(code),
                    "date": date_token.replace("_", "-"),       # 2025-09-02
                    "time": str(time_val) if time_val is not None else None,
                    "status": status,
                    "remark": ""                                # 你目前沒有 remark 欄位就給空字串
                })

        # 5) 依日期時間由新到舊排序
        records.sort(key=lambda r: (r["date"], r["time"] or ""), reverse=True)

        return jsonify(records), 200
    except Exception as e:
        # ★ 這段很重要：失敗也回 JSON，前端才看得到原因
        import traceback
        print('ERROR /api/my_attendance:', e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except:
            pass
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)