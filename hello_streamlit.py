"""
Simple Streamlit Demo - Learn the basics
This is a quick introduction to Streamlit before we build the interview app
"""

import streamlit as st

# Set page title
st.set_page_config(page_title="Streamlit Demo", page_icon="👋")

# Main title
st.title("👋 Welcome to Streamlit!")

# Text
st.write("Streamlit makes it easy to create web apps with Python.")

# Subheader
st.subheader("Try some interactive elements:")

# Text input
name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}! 👋")

# Button
if st.button("Click me!"):
    st.success("Button clicked! ✅")
    st.balloons()

# Slider
age = st.slider("How old are you?", 0, 100, 25)
st.write(f"You selected: {age} years old")

# Selectbox
favorite = st.selectbox(
    "What's your favorite color?",
    ["Red", "Blue", "Green", "Yellow"]
)
st.write(f"Your favorite color is {favorite}")

# Text area
story = st.text_area("Tell me a short story:")
if story:
    st.info(f"Your story has {len(story)} characters")

# Divider
st.divider()

# Info box
st.info("💡 **Tip**: All of these elements update in real-time as you interact with them!")

st.success("Now you're ready to build the AI Granny interview interface!")
