import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API = "http://127.0.0.1:8000"
st.set_page_config(page_title="AI Emotion Analyzer", page_icon="🧠")
st.title("🧠 AI Emotion Analyzer (Full Stack)")
# ---------------- AUTH ----------------
if "token" not in st.session_state:
    st.session_state.token = None

tab1, tab2 = st.tabs(["Login", "Signup"])



# -------- LOGOUT --------
if st.session_state.token:
    with st.sidebar:
        st.success("Logged in")
        if st.button("🚪 Logout"):
            st.session_state.token = None
            st.rerun()





# ---------- LOGIN ----------
with tab1:
    u = st.text_input("Username", key="login_user")
    p = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        resp = requests.post(
            f"{API}/login",
            json={"username": u, "password": p}
        )

        try:
            data = resp.json()
            if "token" in data:
                st.session_state.token = data["token"]
                st.success("Logged in successfully")
            else:
                st.error(data.get("error", "Login failed"))
        except:
            st.error("Invalid response from server")

# ---------- SIGNUP ----------
with tab2:
    su = st.text_input("New Username", key="signup_user")
    sp = st.text_input("New Password", type="password", key="signup_pass")


    if st.button("Signup"):
        resp = requests.post(
            f"{API}/signup",
            json={"username": su, "password": sp}
        )

        try:
            data = resp.json()
            if "message" in data:
                st.success(data["message"])
            else:
                st.error(data.get("error", "Signup failed"))
        except:
            st.error("Invalid response from server")

# ---------------- AI SECTION ----------------
if st.session_state.token:
    st.markdown("---")
    st.subheader("🧠 Emotion Analysis")

    text = st.text_area("Enter text")

    if st.button("Analyze Emotion"):
        resp = requests.post(
            f"{API}/analyze",
            headers={"Authorization": st.session_state.token},
            json={"text": text}
        )

        try:
            data = resp.json()
            if "emotion" in data:
                st.success(f"Emotion: {data['emotion']}")
                st.progress(data["confidence"])
                st.write("Confidence:", round(data["confidence"], 2))
            else:
                st.error("Unauthorized or invalid token")
        except:
            st.error("Invalid response from server")

    if st.button("View History"):
        resp = requests.get(f"{API}/history")
        data = resp.json()

        df = pd.DataFrame(
            data,
            columns=["ID", "Text", "Emotion", "Confidence", "Time"]
        )

        st.dataframe(df)

        st.subheader("📊 Emotion Analytics")
        fig, ax = plt.subplots()
        df["Emotion"].value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)
