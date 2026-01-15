"""
Test voice cloning with ElevenLabs
Run this to verify your API key works before integrating into the app

Usage:
    python test_voice_clone.py                    # List voices and test TTS
    python test_voice_clone.py path/to/audio.wav  # Create voice clone from audio
    python test_voice_clone.py --voice VOICE_ID   # Test specific cloned voice
"""

import sys
import os
sys.path.append('utils')
from voice_helper import (
    create_voice_clone,
    text_to_speech_cloned,
    text_to_speech_elevenlabs,
    get_elevenlabs_voices,
    delete_cloned_voice
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🎤 ElevenLabs Voice Test\n")
print("=" * 50)

# Check for arguments
if len(sys.argv) > 1:
    arg = sys.argv[1]

    if arg == "--voice" and len(sys.argv) > 2:
        # Test specific voice
        voice_id = sys.argv[2]
        print(f"\n🎙️ Testing voice: {voice_id}")

        test_text = "Hello! This is a test of my cloned voice. I hope it sounds like me!"
        print(f"   Text: '{test_text}'")

        success, audio_path, error = text_to_speech_cloned(test_text, voice_id)

        if success:
            print(f"\n✅ Audio generated!")
            print(f"   Path: {audio_path}")
            print(f"   Size: {os.path.getsize(audio_path)} bytes")
            print(f"\n💡 Play the audio to hear the cloned voice")
        else:
            print(f"\n❌ Error: {error}")
        sys.exit(0)

    elif arg == "--delete" and len(sys.argv) > 2:
        # Delete a cloned voice
        voice_id = sys.argv[2]
        print(f"\n🗑️ Deleting voice: {voice_id}")

        confirm = input("Are you sure? (y/n): ")
        if confirm.lower() == 'y':
            success, error = delete_cloned_voice(voice_id)
            if success:
                print("✅ Voice deleted successfully")
            else:
                print(f"❌ Error: {error}")
        sys.exit(0)

    elif os.path.exists(arg):
        # Create voice clone from audio file
        audio_path = arg
        person_name = input("Enter the person's name: ").strip() or "TestPerson"

        print(f"\n📁 Audio file: {audio_path}")
        print(f"   Size: {os.path.getsize(audio_path)} bytes")
        print(f"   Person: {person_name}")

        print("\n🔬 Creating voice clone (this may take 30-60 seconds)...")
        success, voice_id, error = create_voice_clone(audio_path, person_name)

        if not success:
            print(f"\n❌ Voice cloning failed: {error}")
            sys.exit(1)

        print(f"\n✅ Voice cloned successfully!")
        print(f"   Voice ID: {voice_id}")
        print(f"   Name: {person_name}_FamilyVault")

        # Test the cloned voice
        test_text = f"Hello, I am {person_name}. This is my cloned voice speaking."
        print(f"\n🎙️ Testing cloned voice...")

        success, audio_path, error = text_to_speech_cloned(test_text, voice_id)

        if success:
            print(f"✅ Test audio generated: {audio_path}")
            print(f"\n🎉 Voice clone ready to use!")
            print(f"   Save this voice ID: {voice_id}")
        else:
            print(f"⚠️ TTS test failed: {error}")

        sys.exit(0)
    else:
        print(f"❌ File not found: {arg}")
        sys.exit(1)

# Default: List voices and test built-in TTS
print("\n📋 Available Voices:")
print("-" * 40)

success, voices, error = get_elevenlabs_voices()
if not success:
    print(f"❌ Error: {error}")
    sys.exit(1)

cloned_voices = [v for v in voices if v['is_cloned']]
builtin_voices = [v for v in voices if not v['is_cloned']]

print(f"\n🎭 Built-in voices: {len(builtin_voices)}")
for v in builtin_voices[:5]:
    print(f"   - {v['name']}")
if len(builtin_voices) > 5:
    print(f"   ... and {len(builtin_voices) - 5} more")

print(f"\n👤 Your cloned voices: {len(cloned_voices)}")
if cloned_voices:
    for v in cloned_voices:
        print(f"   - {v['name']} ({v['voice_id'][:12]}...)")
else:
    print("   (none yet)")

# Test built-in TTS
print("\n🎙️ Testing TTS with Sarah voice...")
test_text = "Hello dear! Let me tell you a story from my childhood."
success, audio_path, error = text_to_speech_elevenlabs(test_text, voice_name="Sarah")

if success:
    print(f"✅ Audio generated: {os.path.getsize(audio_path)} bytes")
    print(f"   Path: {audio_path}")
else:
    print(f"❌ Error: {error}")

print("\n" + "=" * 50)
print("Usage:")
print("  python test_voice_clone.py audio.wav   # Create clone from audio")
print("  python test_voice_clone.py --voice ID  # Test a specific voice")
print("  python test_voice_clone.py --delete ID # Delete a cloned voice")
