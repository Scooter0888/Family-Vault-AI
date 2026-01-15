"""
Safari-compatible test version
"""
import streamlit as st

st.title("🏛️ Family Vault - Safari Test")

# Simple session state
if 'test' not in st.session_state:
    st.session_state.test = "ready"

st.write("✅ App loaded successfully in Safari!")

# Test file upload
st.subheader("Test Audio Upload")

uploaded_file = st.file_uploader(
    "Upload an audio file",
    type=["mp3", "wav", "m4a"],
    help="Test uploading an audio file"
)

if uploaded_file is not None:
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    st.write(f"Type: {uploaded_file.type}")
    st.write(f"Size: {len(uploaded_file.getbuffer())} bytes")
