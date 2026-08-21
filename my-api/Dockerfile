# ใช้ Python เวอร์ชันน้ำหนักเบา
FROM python:3.10-slim

# ตั้งค่าโฟลเดอร์ทำงานข้างใน Docker
WORKDIR /app

# ก๊อปปี้ไฟล์ requirements.txt ไปติดตั้งไลบรารี
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดทั้งหมด (main.py) เข้าไป
COPY . .

# เปิดประตูพอร์ต 8000
EXPOSE 8000

# คำสั่งสำหรับรัน FastAPI ตอนเริ่มเปิดกล่อง
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]