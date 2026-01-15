"""
Audio Helper Functions
Functions for recording and transcribing audio for Family Vault interviews
"""

import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_bytes, filename="recording.wav", translate_to_english=False):
    """
    Transcribe audio bytes using OpenAI Whisper API

    Args:
        audio_bytes: Audio data from st.audio_input (UploadedFile object)
        filename (str): Filename for the temporary audio file
        translate_to_english (bool): If True, translates non-English audio to English

    Returns:
        str: Transcribed/translated text, or None if transcription fails
    """

    temp_file_path = None

    try:
        # Create a temporary file to store the audio
        # OpenAI API requires a file object, not just bytes
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as temp_audio:
            temp_file_path = temp_audio.name
            # Write the audio bytes to the temp file
            # st.audio_input returns UploadedFile, try different methods to get bytes
            try:
                # Try getbuffer() first (recommended for UploadedFile)
                audio_data = audio_bytes.getbuffer()
            except AttributeError:
                # Fallback: try read() method
                try:
                    audio_bytes.seek(0)  # Reset to beginning
                    audio_data = audio_bytes.read()
                except:
                    # Last resort: try getvalue()
                    audio_data = audio_bytes.getvalue()

            temp_audio.write(audio_data)

        # Open the temp file and send to OpenAI Whisper API
        with open(temp_file_path, 'rb') as audio_file:
            if translate_to_english:
                # Use translations endpoint - automatically detects language and translates to English
                transcript = client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            else:
                # Use transcriptions endpoint - transcribes in original language
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

        # Return the transcribed text
        return transcript.strip() if transcript else None

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error transcribing audio: {error_msg}")
        print(f"Full traceback: {traceback.format_exc()}")

        # Provide user-friendly error messages
        if "rate_limit" in error_msg.lower():
            print("⚠️ Rate limit reached. Please wait a moment and try again.")
        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            print("⚠️ API key issue. Please check your OpenAI API key in the .env file.")
        elif "insufficient_quota" in error_msg.lower():
            print("⚠️ OpenAI account has insufficient credits. Please add credits at platform.openai.com.")
        elif "invalid" in error_msg.lower() and "audio" in error_msg.lower():
            print("⚠️ Invalid audio format. Please try recording again.")
        elif "getbuffer" in error_msg.lower() or "attribute" in error_msg.lower():
            print(f"⚠️ Audio format error. Audio type: {type(audio_bytes)}")
        else:
            print(f"⚠️ Unexpected error: {error_msg}")

        return None

    finally:
        # Clean up: delete the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not delete temp file: {cleanup_error}")


def test_transcription():
    """
    Test function to verify audio transcription works
    This would require a real audio file to test properly
    """

    print("Audio transcription helper loaded successfully!")
    print("Note: Actual testing requires audio input from st.audio_input widget")
    print("OpenAI Whisper API key:", "✅ Found" if os.getenv("OPENAI_API_KEY") else "❌ Not found")


if __name__ == "__main__":
    # Run test if this file is executed directly
    test_transcription()
