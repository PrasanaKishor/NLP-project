import streamlit as st
import speech_recognition as sr
from langdetect import detect
from mtranslate import translate
from gtts import gTTS
import tempfile
import os
import base64
from pydub import AudioSegment
import io

# Initialize recognizer
recognizer = sr.Recognizer()

# Language code mapping with supported TTS languages
LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'hi': 'Hindi',
    'ta': 'Tamil'
}

# Language to voice mapping for gTTS
TTS_LANGUAGE_MAPPING = {
    'en': 'en',
    'es': 'es',
    'fr': 'fr',
    'de': 'de',
    'it': 'it',
    'pt': 'pt',
    'ru': 'ru',
    'zh': 'zh',
    'ja': 'ja',
    'hi': 'hi',
    'ta': 'ta'
}

def record_audio():
    """Record audio from microphone and save to temporary file"""
    with sr.Microphone() as source:
        st.info("Speak now (3-5 seconds)...")
        audio = recognizer.listen(source, timeout=5)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio.get_wav_data())
        return f.name

def detect_language(text):
    """Detect language of the input text"""
    try:
        lang_code = detect(text)
        return lang_code, LANGUAGES.get(lang_code, lang_code)
    except:
        return None, "Unknown"

def adjust_speed(audio_bytes, speed=1.0):
    """Adjust the speed of audio playback"""
    try:
        # Create audio segment from bytes
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        
        # Speed adjustment
        if speed != 1.0:
            # Change speed while maintaining pitch
            audio = audio.speedup(playback_speed=speed)
        
        # Export to bytes
        with io.BytesIO() as f:
            audio.export(f, format="mp3")
            return f.getvalue()
    except Exception as e:
        st.error(f"Speed adjustment error: {e}")
        return audio_bytes  # Return original if adjustment fails

def text_to_speech(text, language_code, speed=1.0):
    """Convert text to speech using gTTS with speed control"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
        
        # Create TTS object
        tts = gTTS(text=text, lang=TTS_LANGUAGE_MAPPING.get(language_code, 'en'), slow=False)
        tts.save(temp_path)
        
        # Read the generated audio
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
        
        # Adjust speed if needed
        if speed != 1.0:
            audio_bytes = adjust_speed(audio_bytes, speed)
        
        # Play the audio
        st.audio(audio_bytes, format="audio/mp3")
        
        return True
    except Exception as e:
        st.error(f"Text-to-speech error: {e}")
        return False
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

def main():
    st.title("🌍 Voice Language Translator")
    st.write("Record your voice, detect the language, and translate to another language")

    # Initialize session state
    if 'input_text' not in st.session_state:
        st.session_state.input_text = None
    if 'detected_lang' not in st.session_state:
        st.session_state.detected_lang = None
    if 'translated_text' not in st.session_state:
        st.session_state.translated_text = None

    # Record audio section
    if st.button("🎤 Record Voice"):
        try:
            audio_file = record_audio()
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
                st.session_state.input_text = recognizer.recognize_google(audio_data)
            
            if st.session_state.input_text:
                lang_code, lang_name = detect_language(st.session_state.input_text)
                st.session_state.detected_lang = (lang_code, lang_name)
                st.success("Voice recorded successfully!")
        except sr.UnknownValueError:
            st.error("Could not understand audio. Please try again.")
        except sr.RequestError as e:
            st.error(f"Speech recognition service error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            if 'audio_file' in locals() and os.path.exists(audio_file):
                os.unlink(audio_file)

    # Display input if available
    if st.session_state.input_text:
        st.subheader("Original Text")
        st.write(st.session_state.input_text)
        
        if st.session_state.detected_lang:
            st.write(f"Detected language: {st.session_state.detected_lang[1]}")

    # Translation section
    if st.session_state.input_text:
        col1, col2 = st.columns(2)
        with col1:
            target_lang = st.selectbox(
                "Select target language:",
                options=list(LANGUAGES.items()),
                format_func=lambda x: x[1],
                key="target_lang"
            )
        with col2:
            # Speed control slider (1.0 is normal speed)
            speed = st.slider(
                "Speech speed",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="1.0 is normal speed, lower is slower, higher is faster"
            )

        if st.button("Translate"):
            if target_lang:
                try:
                    st.session_state.translated_text = translate(
                        st.session_state.input_text,
                        target_lang[0],
                        'auto'
                    )
                except Exception as e:
                    st.error(f"Translation error: {e}")

    # Display translation if available
    if st.session_state.translated_text:
        st.subheader("Translation")
        st.write(st.session_state.translated_text)
        
        # Text-to-speech with speed control
        target_code = st.session_state.get('target_lang', ('en', 'English'))[0]
        if not text_to_speech(st.session_state.translated_text, target_code, speed):
            st.warning("Couldn't play audio in selected language. Trying English...")
            text_to_speech(st.session_state.translated_text, 'en', speed)

if __name__ == "__main__":
    main()