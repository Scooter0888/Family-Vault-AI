"""
Voice Helper - Text-to-Speech and Voice Cloning
Provides voice output for AI responses in Q&A mode
"""

import os
from openai import OpenAI
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_openai_client():
    """Get OpenAI client with API key"""
    return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Voice options with personality descriptions
VOICE_PROFILES = {
    "Warm Grandmother (Shimmer)": {
        "voice": "shimmer",
        "description": "Warm, friendly female voice - like a caring grandmother",
        "speed": 0.95
    },
    "Calm Grandfather (Onyx)": {
        "voice": "onyx",
        "description": "Deep, calm male voice - like a wise grandfather",
        "speed": 0.95
    },
    "Upbeat & Friendly (Nova)": {
        "voice": "nova",
        "description": "Energetic, cheerful female voice - upbeat storyteller",
        "speed": 1.0
    },
    "Professional Narrator (Alloy)": {
        "voice": "alloy",
        "description": "Neutral, clear voice - professional narrator",
        "speed": 1.0
    },
    "Gentle & Soothing (Echo)": {
        "voice": "echo",
        "description": "Gentle male voice - soothing and reassuring",
        "speed": 0.95
    },
    "Warm Storyteller (Fable)": {
        "voice": "fable",
        "description": "Expressive British accent - engaging storyteller",
        "speed": 1.0
    }
}


def text_to_speech(text, voice_profile="Warm Grandmother (Shimmer)", model="tts-1"):
    """
    Convert text to speech using OpenAI TTS API

    Args:
        text (str): Text to convert to speech
        voice_profile (str): Voice profile name from VOICE_PROFILES
        model (str): TTS model - "tts-1" (faster) or "tts-1-hd" (higher quality)

    Returns:
        tuple: (success: bool, audio_path: str, error: str)
    """
    try:
        # Get OpenAI client
        client = get_openai_client()

        # Get voice settings from profile
        profile = VOICE_PROFILES.get(voice_profile, VOICE_PROFILES["Warm Grandmother (Shimmer)"])
        voice = profile["voice"]
        speed = profile.get("speed", 1.0)

        # Create temporary file for audio (include voice in hash to avoid cache conflicts)
        temp_dir = tempfile.gettempdir()
        unique_key = f"{text}_{voice}_{speed}"  # Include voice and speed in hash
        audio_filename = f"tts_{hash(unique_key) % 10000}.wav"
        audio_path = os.path.join(temp_dir, audio_filename)

        # Generate speech - use 'wav' format for better Safari compatibility
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
            response_format="wav"  # WAV format for Safari compatibility
        )

        # Save to file
        response.stream_to_file(audio_path)

        return True, audio_path, None

    except Exception as e:
        return False, None, str(e)


def get_voice_profiles():
    """
    Get list of available voice profiles

    Returns:
        dict: Voice profiles with descriptions
    """
    return VOICE_PROFILES


def get_voice_profile_names():
    """
    Get list of voice profile names for UI selection

    Returns:
        list: Voice profile names
    """
    return list(VOICE_PROFILES.keys())


# Voice cloning functions using ElevenLabs

# ElevenLabs model to use (newer models work on free tier)
ELEVENLABS_MODEL = "eleven_turbo_v2_5"


def create_voice_clone(audio_file_path, person_name):
    """
    Create a voice clone from audio samples using ElevenLabs

    Args:
        audio_file_path (str): Path to audio file (WAV, MP3, etc.) - at least 30 seconds of clear speech
        person_name (str): Name of person for voice clone

    Returns:
        tuple: (success: bool, voice_id: str, error: str)
    """
    try:
        from elevenlabs.client import ElevenLabs
        import os

        # Get API key
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key or api_key == 'your_elevenlabs_api_key_here':
            return False, None, "ElevenLabs API key not set. Please add ELEVENLABS_API_KEY to .env file"

        # Initialize client
        client = ElevenLabs(api_key=api_key)

        # Create voice clone using IVC (Instant Voice Cloning)
        # Note: ElevenLabs requires at least 30 seconds of clear audio
        voice = client.voices.ivc.create(
            name=f"{person_name}_FamilyVault",
            description=f"Cloned voice of {person_name} from Family Vault interview",
            files=[audio_file_path]  # Pass file path
        )

        return True, voice.voice_id, None

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "401" in error_msg:
            return False, None, "Invalid ElevenLabs API key. Please check your .env file"
        elif "audio" in error_msg.lower() or "file" in error_msg.lower():
            return False, None, f"Audio issue: {error_msg}. Please use at least 30 seconds of clear audio"
        else:
            return False, None, f"Voice cloning failed: {error_msg}"


def text_to_speech_elevenlabs(text, voice_id=None, voice_name="Sarah"):
    """
    Convert text to speech using ElevenLabs (built-in or cloned voice)

    Args:
        text (str): Text to convert to speech
        voice_id (str): Voice ID for cloned voice (optional)
        voice_name (str): Built-in voice name if no voice_id provided

    Returns:
        tuple: (success: bool, audio_path: str, error: str)
    """
    try:
        from elevenlabs.client import ElevenLabs
        import os
        import tempfile

        # Get API key
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key or api_key == 'your_elevenlabs_api_key_here':
            return False, None, "ElevenLabs API key not set"

        # Initialize client
        client = ElevenLabs(api_key=api_key)

        # Use provided voice_id or look up by name
        if not voice_id:
            # Get voice by name
            voices = client.voices.get_all()
            for v in voices.voices:
                if voice_name.lower() in v.name.lower():
                    voice_id = v.voice_id
                    break
            if not voice_id:
                return False, None, f"Voice '{voice_name}' not found"

        # Generate speech
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=ELEVENLABS_MODEL
        )

        # Save to temp file
        temp_dir = tempfile.gettempdir()
        unique_key = f"{text}_{voice_id}"
        audio_filename = f"elevenlabs_tts_{hash(unique_key) % 10000}.mp3"
        audio_path = os.path.join(temp_dir, audio_filename)

        # Write audio bytes to file
        with open(audio_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)

        return True, audio_path, None

    except Exception as e:
        return False, None, f"ElevenLabs TTS failed: {str(e)}"


def text_to_speech_cloned(text, voice_id, model=None):
    """
    Convert text to speech using cloned voice from ElevenLabs
    (Wrapper for backwards compatibility)

    Args:
        text (str): Text to convert to speech
        voice_id (str): Voice ID from create_voice_clone()
        model (str): Ignored - uses ELEVENLABS_MODEL

    Returns:
        tuple: (success: bool, audio_path: str, error: str)
    """
    return text_to_speech_elevenlabs(text, voice_id=voice_id)


def get_elevenlabs_voices():
    """
    Get list of available ElevenLabs voices (including cloned ones)

    Returns:
        tuple: (success: bool, voices: list, error: str)
    """
    try:
        from elevenlabs.client import ElevenLabs
        import os

        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            return False, [], "ElevenLabs API key not set"

        client = ElevenLabs(api_key=api_key)
        voices = client.voices.get_all()

        voice_list = []
        for v in voices.voices:
            voice_list.append({
                'name': v.name,
                'voice_id': v.voice_id,
                'category': v.category if hasattr(v, 'category') else 'unknown',
                'is_cloned': 'cloned' in (v.category or '').lower() or 'FamilyVault' in v.name
            })

        return True, voice_list, None

    except Exception as e:
        return False, [], f"Failed to get voices: {str(e)}"


def delete_cloned_voice(voice_id):
    """
    Delete a cloned voice from ElevenLabs

    Args:
        voice_id (str): Voice ID to delete

    Returns:
        tuple: (success: bool, error: str)
    """
    try:
        from elevenlabs.client import ElevenLabs
        import os

        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            return False, "ElevenLabs API key not set"

        client = ElevenLabs(api_key=api_key)
        client.voices.delete(voice_id)

        return True, None

    except Exception as e:
        return False, f"Failed to delete voice: {str(e)}"


def clone_voice_from_audio_bytes(audio_bytes, person_name):
    """
    Create a voice clone from audio bytes (e.g., from Streamlit audio input)

    Args:
        audio_bytes: Audio data as bytes or file-like object
        person_name (str): Name of person for voice clone

    Returns:
        tuple: (success: bool, voice_id: str, error: str)
    """
    try:
        from elevenlabs.client import ElevenLabs
        import os
        import tempfile
        import subprocess

        # Get API key
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key or api_key == 'your_elevenlabs_api_key_here':
            return False, None, "ElevenLabs API key not set"

        # Handle both bytes and file-like objects
        if hasattr(audio_bytes, 'read'):
            audio_data = audio_bytes.read()
        elif hasattr(audio_bytes, 'getvalue'):
            audio_data = audio_bytes.getvalue()
        elif hasattr(audio_bytes, 'getbuffer'):
            audio_data = audio_bytes.getbuffer().tobytes()
        else:
            audio_data = audio_bytes

        temp_dir = tempfile.gettempdir()
        safe_name = person_name.replace(' ', '_').replace("'", "").replace('"', '')

        # Detect audio format from magic bytes
        if audio_data[:4] == b'RIFF':
            input_ext = '.wav'
        elif audio_data[:4] == b'OggS':
            input_ext = '.ogg'
        elif audio_data[:4] == b'\x1aE\xdf\xa3':
            input_ext = '.webm'
        elif audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
            input_ext = '.mp3'
        else:
            input_ext = '.ogg'  # Streamlit often uses ogg

        # Try approach 1: Send raw audio directly (ElevenLabs supports webm, ogg, wav, mp3)
        raw_audio_path = os.path.join(temp_dir, f"voice_sample_{safe_name}{input_ext}")
        with open(raw_audio_path, 'wb') as f:
            f.write(audio_data)

        temp_audio_path = raw_audio_path  # Start with raw file

        # Check file size
        file_size = os.path.getsize(raw_audio_path)
        if file_size < 10000:
            return False, None, f"Audio too short ({file_size} bytes). Need at least 30 seconds."

        # Try to use raw file first, if ElevenLabs rejects it, convert with ffmpeg
        client = ElevenLabs(api_key=api_key)

        try:
            # First attempt: use raw audio file
            voice = client.voices.ivc.create(
                name=f"{person_name}_FamilyVault",
                description=f"Cloned voice of {person_name} from Family Vault interview",
                files=[raw_audio_path]
            )
            # Clean up
            try:
                os.remove(raw_audio_path)
            except:
                pass
            return True, voice.voice_id, None

        except Exception as first_error:
            # If raw file failed, try converting with ffmpeg
            first_error_msg = str(first_error)
            if "invalid_content" in first_error_msg.lower() or "corrupted" in first_error_msg.lower():
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

                    # Convert to WAV (most reliable format)
                    converted_path = os.path.join(temp_dir, f"converted_voice_{safe_name}.wav")
                    result = subprocess.run(
                        [ffmpeg_path, '-y', '-i', raw_audio_path,
                         '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1',
                         converted_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0 and os.path.exists(converted_path):
                        temp_audio_path = converted_path
                        # Try again with converted file
                        voice = client.voices.ivc.create(
                            name=f"{person_name}_FamilyVault",
                            description=f"Cloned voice of {person_name} from Family Vault interview",
                            files=[temp_audio_path]
                        )
                        # Clean up
                        for f in [raw_audio_path, converted_path]:
                            try:
                                os.remove(f)
                            except:
                                pass
                        return True, voice.voice_id, None
                    else:
                        return False, None, f"Audio conversion failed: {result.stderr[:200]}"
                except Exception as conv_error:
                    return False, None, f"Conversion failed: {str(conv_error)}"
            else:
                # Different error, not format related
                raise first_error

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            return False, None, "Invalid ElevenLabs API key"
        elif "insufficient" in error_msg.lower() or "quota" in error_msg.lower():
            return False, None, "ElevenLabs quota exceeded. Check your plan limits."
        else:
            return False, None, f"Voice cloning failed: {error_msg}"


def combine_audio_samples(audio_samples):
    """
    Combine multiple audio samples into one file for voice cloning

    Args:
        audio_samples: List of dicts with 'audio_data' (bytes)

    Returns:
        tuple: (success: bool, combined_audio_path: str, error: str)
    """
    try:
        import tempfile
        import os

        if not audio_samples:
            return False, None, "No audio samples provided"

        # Calculate total size
        total_size = sum(len(s['audio_data']) for s in audio_samples)

        if total_size < 50000:  # Less than ~50KB
            return False, None, f"Audio too short ({total_size} bytes). Need more recordings."

        # For simplicity, use the largest sample (best quality likely)
        # In production, could use pydub to concatenate
        largest_sample = max(audio_samples, key=lambda s: len(s['audio_data']))

        # Save to temp file
        temp_dir = tempfile.gettempdir()
        combined_path = os.path.join(temp_dir, "combined_voice_sample.wav")

        with open(combined_path, 'wb') as f:
            f.write(largest_sample['audio_data'])

        return True, combined_path, None

    except Exception as e:
        return False, None, f"Failed to combine audio: {str(e)}"


def auto_clone_voice_from_samples(audio_samples, person_name):
    """
    Automatically create a voice clone from collected interview audio samples

    Args:
        audio_samples: List of dicts with 'audio_data' (bytes)
        person_name: Name of the person

    Returns:
        tuple: (success: bool, voice_id: str, error: str)
    """
    try:
        from elevenlabs.client import ElevenLabs
        import os
        import tempfile
        import subprocess

        if not audio_samples:
            return False, None, "No audio samples collected during interview"

        # Get API key
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            return False, None, "ElevenLabs API key not set"

        # Find the largest/best audio sample
        total_size = sum(len(s['audio_data']) for s in audio_samples)

        if total_size < 30000:  # Need at least ~30KB
            return False, None, f"Not enough audio recorded ({total_size} bytes). Need more voice samples."

        # Use the largest sample for best quality
        largest_sample = max(audio_samples, key=lambda s: len(s['audio_data']))
        audio_data = largest_sample['audio_data']

        temp_dir = tempfile.gettempdir()
        safe_name = person_name.replace(' ', '_').replace("'", "").replace('"', '')

        # Detect audio format from magic bytes
        if audio_data[:4] == b'RIFF':
            input_ext = '.wav'
        elif audio_data[:4] == b'OggS':
            input_ext = '.ogg'
        elif audio_data[:4] == b'\x1aE\xdf\xa3':
            input_ext = '.webm'
        elif audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
            input_ext = '.mp3'
        else:
            input_ext = '.ogg'  # Streamlit often uses ogg

        # Save raw audio
        raw_audio_path = os.path.join(temp_dir, f"auto_voice_{safe_name}{input_ext}")
        with open(raw_audio_path, 'wb') as f:
            f.write(audio_data)

        # Initialize client
        client = ElevenLabs(api_key=api_key)

        try:
            # First attempt: use raw audio file directly
            voice = client.voices.ivc.create(
                name=f"{person_name}_FamilyVault",
                description=f"Auto-cloned voice of {person_name} from Family Vault interview",
                files=[raw_audio_path]
            )
            # Clean up
            try:
                os.remove(raw_audio_path)
            except:
                pass
            return True, voice.voice_id, None

        except Exception as first_error:
            # If raw file failed, try converting with ffmpeg
            first_error_msg = str(first_error)
            if "invalid_content" in first_error_msg.lower() or "corrupted" in first_error_msg.lower():
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

                    # Convert to WAV
                    converted_path = os.path.join(temp_dir, f"converted_auto_voice_{safe_name}.wav")
                    result = subprocess.run(
                        [ffmpeg_path, '-y', '-i', raw_audio_path,
                         '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1',
                         converted_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0 and os.path.exists(converted_path):
                        # Try again with converted file
                        voice = client.voices.ivc.create(
                            name=f"{person_name}_FamilyVault",
                            description=f"Auto-cloned voice of {person_name} from Family Vault interview",
                            files=[converted_path]
                        )
                        # Clean up
                        for f in [raw_audio_path, converted_path]:
                            try:
                                os.remove(f)
                            except:
                                pass
                        return True, voice.voice_id, None
                    else:
                        return False, None, f"Audio conversion failed: {result.stderr[:200]}"
                except Exception as conv_error:
                    return False, None, f"Conversion failed: {str(conv_error)}"
            else:
                raise first_error

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            return False, None, "Invalid ElevenLabs API key"
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return False, None, "ElevenLabs quota exceeded"
        else:
            return False, None, f"Voice cloning failed: {error_msg}"


def update_profile_voice_id(profile_path, voice_id):
    """
    Update a parent profile JSON file with a cloned voice ID

    Args:
        profile_path (str): Path to the parent profile JSON file
        voice_id (str): ElevenLabs voice ID to save

    Returns:
        tuple: (success: bool, error: str)
    """
    try:
        import json

        # Read existing profile
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        # Add voice_id
        profile['voice_id'] = voice_id
        profile['voice_cloned_at'] = __import__('datetime').datetime.now().isoformat()

        # Save updated profile
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        return True, None

    except Exception as e:
        return False, f"Failed to update profile: {str(e)}"


def get_profile_voice_id(profile_path):
    """
    Get the cloned voice ID from a parent profile

    Args:
        profile_path (str): Path to the parent profile JSON file

    Returns:
        str or None: Voice ID if exists, None otherwise
    """
    try:
        import json

        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        return profile.get('voice_id')

    except:
        return None
