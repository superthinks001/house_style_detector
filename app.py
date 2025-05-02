import streamlit as st
from predict_house_style import predict_style
import tempfile
import os
from PIL import Image
import cv2

st.set_page_config(page_title="House Style Detector", layout="wide")
st.title("🏠 House Style Detection with AI")

uploaded_files = st.file_uploader("Upload one or more house images", accept_multiple_files=True, type=["jpg", "png", "jpeg"])

if uploaded_files:
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        preds, result_obj = predict_style(tmp_path)

        col1, col2 = st.columns(2)
        with col1:
            st.image(Image.open(tmp_path), caption="Original", use_column_width=True)
        with col2:
            st.image(result_obj.plot(), caption="Prediction", use_column_width=True)

        for pred in preds:
            label = pred["label"]
            conf = int(pred["confidence"] * 100)
            st.markdown(f"🔎 **Prediction:** `{label}` — **Confidence:** {conf}%")
            correction = st.selectbox(f"Is this prediction correct for {file.name}?", ["Yes", "No - Wrong Style"], key=file.name + label)

        os.unlink(tmp_path)
