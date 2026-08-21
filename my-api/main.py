from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@db:5432/mydb")

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error connecting to database: {e}")

@app.on_event("startup")
def startup_event():
    init_db()

# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

class UserUpdate(BaseModel):
    username: str
    password: str


# ==========================================
# 1. Authentication (ล็อกอิน/สมัคร)
# ==========================================

@app.post("/register")
def register(user: UserCreate):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username นี้ถูกใช้งานแล้ว")
        
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, user.password))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "สมัครสมาชิกสำเร็จ!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login(user: UserCreate):
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (user.username, user.password))
        db_user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not db_user:
            raise HTTPException(status_code=400, detail="Username หรือ Password ไม่ถูกต้อง")
            
        return {"message": "เข้าสู่ระบบสำเร็จ!", "username": db_user["username"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/logout")
def logout():
    # ฝั่ง API สามารถเคลียร์สถานะ Token/Session ได้ (ในที่นี้ทำรองรับตามโจทย์)
    return {"message": "ออกจากระบบสำเร็จ"}

@app.post("/change-password")
def change_password(data: ChangePasswordRequest):
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (data.username, data.old_password))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")
            
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (data.new_password, data.username))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "เปลี่ยนรหัสผ่านสำเร็จ"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 2. User Management (จัดการข้อมูล)
# ==========================================

@app.get("/me")
def get_me(username: str):
    # จำลองการดึงข้อมูลตัวเองผ่าน Query Parameter เช่น /me?username=Best
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, username FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งานนี้")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบ User นี้")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
def get_all_users(limit: int = 10, offset: int = 0):
    # รองรับ Pagination (limit, offset) ตามโจทย์
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, username FROM users LIMIT %s OFFSET %s", (limit, offset))
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"users": users, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username = %s, password = %s WHERE id = %s", (user.username, user.password, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": f"อัปเดตข้อมูล User ID {user_id} สำเร็จ"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": f"ลบ User ID {user_id} สำเร็จ"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/check-username/{name}")
def check_username(name: str):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (name,))
        exists = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if exists:
            return {"available": False, "message": "Username นี้ถูกใช้งานแล้ว"}
        return {"available": True, "message": "Username นี้สามารถใช้งานได้"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))