# app.py – Updated with Feedback + BigQuery Logging

import streamlit as st
from predict_house_style import predict_style
from google.cloud import bigquery
from google.oauth2 import service_account
import tempfile
import os
from PIL import Image
import uuid
import datetime

# ---------- CONFIGURE ----------
KEY_FILE = "ai-architectural-classifier-e1c42811d822.json"
TABLE_ID = "ai-architectural-classifier.house_style_feedback.user_feedback"

# ---------- AUTH + BIGQUERY ----------
import json
# Pulling the service account JSON from Streamlit secrets
json_key = st.secrets["GOOGLE_CREDENTIALS_JSON"]

# Creating credentials from the in-memory string
credentials = service_account.Credentials.from_service_account_info(json.loads(json_key))

# Initializing BigQuery client
bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# ---------- FEEDBACK LOGGER ----------
def log_feedback(image_name, predicted_style, predicted_conf, is_correct, correct_style=None):
    row = {
        "image_id": str(uuid.uuid4()),
        "image_name": image_name,
        "predicted_style": predicted_style,
        "predicted_confidence": predicted_conf,
        "is_correct": is_correct,
        "correct_style": correct_style if not is_correct else None,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    errors = bq_client.insert_rows_json(TABLE_ID, [row])
    if errors:
        st.error(f"Failed to log feedback: {errors}")
    else:
        st.success("✅ Feedback submitted!")

# ---------- UI ----------
st.title("🏠 House Style Detector")
uploaded_file = st.file_uploader("Upload a house image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # Predict using model
    pred_img, predicted_style, predicted_conf = predict_style(tmp_path)

    col1, col2 = st.columns(2)
    with col1:
        st.image(Image.open(tmp_path), caption="Original Image", use_column_width=True)
    with col2:
        st.image(pred_img, caption=f"Prediction: {predicted_style} ({predicted_conf:.0%})", use_column_width=True)

    # User Feedback
    st.markdown("---")
    st.subheader("Was this prediction correct?")
    feedback = st.radio("", ["Yes", "No - wrong style"], horizontal=True)

    correct_style = None
    if feedback == "No - wrong style":
        correct_style = st.selectbox("What is the correct style?", [
            "Mediterranean", "Tudor", "Cape Cod", "Colonial", "Craftsman",
            "Mid-century Modern", "Contemporary", "Victorian", "Janes Village"])

    if st.button("Submit Feedback"):
        is_correct = feedback == "Yes"
        log_feedback(
            image_name=uploaded_file.name,
            predicted_style=predicted_style,
            predicted_conf=predicted_conf,
            is_correct=is_correct,
            correct_style=correct_style
        )
