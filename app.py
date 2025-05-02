# app.py – Updated with Feedback + BigQuery Logging

import streamlit as st
from predict_house_style import predict_style
import tempfile
import os
from PIL import Image
import json
import uuid
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account

# ---------- AUTH + BIGQUERY ----------
import json
# Pulling the service account JSON from Streamlit secrets
json_key = st.secrets["GOOGLE_CREDENTIALS_JSON"]

# Creating credentials from the in-memory string
credentials = service_account.Credentials.from_service_account_info(json.loads(json_key))

# Initializing BigQuery client
bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)

PROJECT_ID = "ai-architectural-classifier"
TABLE_ID = "ai-architectural-classifier.house_style_feedback.user_feedback"

def log_feedback_to_bigquery(image_name, predicted_style, confidence, is_correct, correct_style):
    row = {
        "image_id": str(uuid.uuid4()),
        "image_name": image_name,
        "predicted_style": predicted_style,
        "predicted_confidence": float(confidence),
        "is_correct": is_correct,
        "correct_style": correct_style if not is_correct else None,
        "timestamp": datetime.utcnow()
    }

    errors = bq_client.insert_rows_json(TABLE_ID, [row])
    if errors:
        st.error(f"❌ Failed to log feedback: {errors}")
    else:
        st.success("✅ Feedback saved successfully!")

# ----------- UI + PREDICTION -----------
st.set_page_config(page_title="House Style Classifier", layout="wide")
st.title("🏠 House Style Detector")

uploaded_file = st.file_uploader("Upload a house image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name

    col1, col2 = st.columns(2)
    with col1:
        st.image(uploaded_file, caption="Original Image", use_column_width=True)

    with col2:
        pred_img, predicted_label, confidence = predict_style(temp_path)
        st.image(pred_img, caption=f"Prediction: {predicted_label} ({confidence:.2%})", use_column_width=True)

    # Feedback Section
    st.subheader("Feedback")
    user_feedback = st.radio("Was this prediction correct?", ["Yes", "No"], horizontal=True)

    correct_style = None
    if user_feedback == "No":
        correct_style = st.selectbox("What is the correct style?", [
            "Mediterranean", "Tudor", "Cape Cod", "Colonial", "Craftsman", 
            "Mid-century Modern", "Contemporary", "Victorian", "Janes Village"])

    if st.button("Submit Feedback"):
        log_feedback_to_bigquery(
            image_name=uploaded_file.name,
            predicted_style=predicted_label,
            confidence=confidence,
            is_correct=(user_feedback == "Yes"),
            correct_style=correct_style if user_feedback == "No" else None
        )

    # Cleanup
    os.remove(temp_path)
