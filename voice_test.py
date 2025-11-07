import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import os

def listen_and_respond():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎙️ Speak something...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {text}")
        
        # Simple AI-style reply (we'll replace this with real ChatGPT soon)
        reply = f"You said '{text}', nice to meet you Rohit!"
        print(f"🤖 Bot: {reply}")

        # Convert reply to speech
        tts = gTTS(reply)
        tts.save("reply.mp3")
        playsound("reply.mp3")
        os.remove("reply.mp3")

    except sr.UnknownValueError:
        print("Sorry, I couldn’t understand your voice.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    listen_and_respond()
