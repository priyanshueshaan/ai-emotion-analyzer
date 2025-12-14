from fastapi import FastAPI, Header
from transformers import pipeline
import sqlite3
from datetime import datetime
from jose import jwt
from passlib.context import CryptContext
import sqlite3
from fastapi.middleware.cors import CORSMiddleware


# ---------------- SECURITY ----------------
SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- APP ----------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # OK for demo/project
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------- AI MODEL ----------------
model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=True
)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    emotion TEXT,
    confidence REAL,
    timestamp TEXT
)
""")
conn.commit()

# ---------------- HELPERS ----------------
def hash_password(password: str):
    # bcrypt limit is 72 bytes
    password = password.encode("utf-8")

    if len(password) > 72:
        password = password[:72]  # safe truncate

    return pwd_context.hash(password)


def verify_password(password, hashed):
    password = password.encode("utf-8")
    if len(password) > 72:
        password = password[:72]
    return pwd_context.verify(password, hashed)


def create_token(username):
    return jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except:
        return False

# ---------------- AUTH APIs ----------------
@app.post("/signup")
def signup(data: dict):
    try:
        username = data.get("username", "").lower().strip()
        password = data.get("password", "")

        if not username or not password:
            return {"error": "Username and password required"}
        if len(password.encode("utf-8")) > 72:
            return {"error": "Password too long (max 72 bytes)"}

        hashed = hash_password(password)

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()

        return {"message": "User created"}

    except sqlite3.IntegrityError:
        return {"error": "User already exists"}

    except Exception as e:
        # THIS is the missing safety net
        return {"error": f"Server error: {str(e)}"}

@app.post("/login")
def login(data: dict):
    username = data["username"].lower().strip()
    password = data["password"]

    cursor.execute(
        "SELECT password FROM users WHERE username=?",
        (username,)
    )
    row = cursor.fetchone()

    if row and verify_password(password, row[0]):
        return {"token": create_token(username)}

    return {"error": "Invalid credentials"}

# ---------------- AI API ----------------
@app.post("/analyze")
def analyze_sentiment(data: dict, authorization: str = Header(None)):
    if not authorization or not verify_token(authorization):
        return {"error": "Unauthorized"}

    text = data["text"]
    results = model(text)[0]

    top_emotion = max(results, key=lambda x: x["score"])
    emotion = top_emotion["label"]
    confidence = top_emotion["score"]

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO history (text, emotion, confidence, timestamp) VALUES (?, ?, ?, ?)",
        (text, emotion, confidence, time)
    )
    conn.commit()

    return {
        "emotion": emotion,
        "confidence": confidence,
        "timestamp": time
    }

@app.get("/history")
def history():
    cursor.execute("SELECT * FROM history ORDER BY id DESC")
    return cursor.fetchall()
