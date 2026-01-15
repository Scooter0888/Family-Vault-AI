import streamlit as st

st.title("Minimal Audio Test")

st.write("Testing st.audio_input with minimal code")

try:
    audio = st.audio_input("Record audio")

    if audio is not None:
        st.success("✅ Audio recorded!")
        st.write(f"Type: {type(audio)}")
        st.write(f"Size: {len(audio.getbuffer())} bytes")
    else:
        st.info("No audio yet")
except Exception as e:
    st.error(f"Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
