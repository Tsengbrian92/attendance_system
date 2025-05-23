from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL 連接資訊
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Aa0901155900",  # 替換為你的 MySQL 密碼
    "database": "studentif"   # 替換為你的資料庫名稱
}

@app.route('/receive_uid', methods=['POST'])
def receive_uid():
    data = request.get_json()
    
    if not data or "uid" not in data:
        return jsonify({"status": "error", "message": "Invalid data"}), 400  # 400 Bad Request
    
    uid = data["uid"]  # **現在即使 `try` 失敗，uid 變數也已經定義**
    
    try:
        # **連接 MySQL**
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # **插入資料**
        insert_query = "INSERT INTO test (cardID) VALUES (%s)"
        cursor.execute(insert_query, (uid,))

        # **提交變更**
        connection.commit()

        print(f"Received UID from Python: {uid}")  # ✅ 這裡 uid 變數已經有值
        return jsonify({"status": "success", "uid": uid}), 200

    except mysql.connector.Error as e:
        return jsonify({"status": "error", "message": f"資料庫錯誤: {str(e)}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


