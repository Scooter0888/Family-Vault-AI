"""
Simple TTS Test - Debug voice features
"""
import streamlit as st
import sys
import os

sys.path.append('utils')
from voice_helper import text_to_speech, get_voice_profile_names

st.title("🔊 Text-to-Speech Test")

st.write("This is a simple test to verify TTS is working.")

# Voice selector
voice_profiles = get_voice_profile_names()
selected_voice = st.selectbox("Select Voice:", voice_profiles)

# Test text
test_text = st.text_area(
    "Text to speak:",
    value="Hello! This is a test of the text to speech system.",
    height=100
)

if st.button("🔊 Generate Speech", type="primary"):
    with st.spinner("Generating audio..."):
        try:
            success, audio_path, error = text_to_speech(test_text, selected_voice)

            st.write(f"**Success:** {success}")
            st.write(f"**Audio Path:** {audio_path}")
            st.write(f"**Error:** {error}")

            if success and audio_path:
                if os.path.exists(audio_path):
                    st.success(f"✅ File exists at: {audio_path}")
                    st.write(f"File size: {os.path.getsize(audio_path)} bytes")

                    # Try to play it
                    try:
                        with open(audio_path, 'rb') as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format='audio/wav')
                        st.success("✅ Audio player loaded! (WAV format for Safari compatibility)")
                    except Exception as e:
                        st.error(f"❌ Failed to play audio: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                else:
                    st.error(f"❌ File does not exist at: {audio_path}")
            else:
                st.error(f"❌ TTS generation failed: {error}")

        except Exception as e:
            st.error(f"❌ Exception: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
