import serial
import requests

SERIAL_PORT = "COM11"  # Windows
BAUD_RATE = 115200
API_URL = "http://26.8.220.101:5000/receive_uid"  # Flask API 端點

try:
    # 連接 Arduino
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to Arduino on {SERIAL_PORT}!")

    while True:
        uid = ser.readline().decode(errors='ignore').strip()  # 讀取 UID
        
        if uid:
            print(f"Received UID: {uid}")  # 顯示 UID
            payload = {"uid": uid}  # **確保 JSON 格式正確**
            print(f"Sending JSON: {payload}")  # **Debug 輸出**

            try:
                response = requests.post(API_URL, json=payload, timeout=2)
                print(f"Server Response: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"API Request Failed: {e}")
        else:
            print("Waiting for UID...")  # **如果沒有收到資料，印出等待訊息**

except serial.SerialException as e:
    print(f"Error: Could not open serial port {SERIAL_PORT}: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")