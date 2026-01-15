"""
Test st.audio_input functionality
"""
import streamlit as st

st.title("Audio Input Test")

# Check if audio_input exists
if hasattr(st, 'audio_input'):
    st.success("✅ st.audio_input is available")

    audio = st.audio_input("Test recording")

    if audio:
        st.success(f"Audio received! Type: {type(audio)}")
        st.write(f"Audio size: {len(audio.getbuffer())} bytes")

        # Try to display it
        st.audio(audio)
    else:
        st.info("No audio recorded yet")
else:
    st.error("❌ st.audio_input is NOT available in this Streamlit version")
    st.write(f"Streamlit version: {st.__version__}")
