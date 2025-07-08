import speech_recognition as sr
import requests
import traceback
from gtts import gTTS
import os
import signal
import subprocess
import threading

def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("response.mp3")
    # Play with afplay (macOS)
    player = subprocess.Popen(["afplay", "response.mp3"])
    return player

def stop_speaking(player):
    if player and player.poll() is None:
        os.kill(player.pid, signal.SIGTERM)

def ask_llama3(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3",
        "prompt": f"Please answer briefly: {prompt}",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "max_tokens": 150
        }
    }
    try:
        response = requests.post(url, json=data)
        print("Raw Ollama response:", response.text)
        if response.status_code == 200:
            json_data = response.json()
            return json_data.get("response") or json_data.get("message") or "No valid response from Llama 3."
        else:
            return f"Sorry, I couldn't get a response from Llama 3. Status code: {response.status_code}"
    except Exception as e:
        print("Llama 3 communication error:", e)
        traceback.print_exc()
        return f"Error communicating with Llama 3: {e}"

def listen(prompt="Listening..."):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(prompt)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=7)
            command = r.recognize_google(audio)
            print("You said:", command)
            return command.lower()
        except sr.WaitTimeoutError:
            print("Listening timed out, no speech detected.")
            return ""
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            return ""
        except Exception as e:
            print("Speech recognition error:", e)
            traceback.print_exc()
            return ""

def listen_for_interrupt(interrupt_event):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        while not interrupt_event.is_set():
            try:
                print("Say 'stop' to interrupt...")
                audio = r.listen(source, timeout=2, phrase_time_limit=2)
                command = r.recognize_google(audio).lower()
                print("Interrupt heard:", command)
                if any(word in command for word in ["stop", "exit", "quit"]):
                    interrupt_event.set()
                    break
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print("Error while listening for interrupt:", e)
                traceback.print_exc()
                continue

def main():
    print("Hello! How can I help you?")
    while True:
        command = listen()
        if not command:
            continue
        if any(word in command for word in ["stop", "exit", "quit"]):
            player = speak("Goodbye!")
            player.wait()
            break
        response = ask_llama3(command)
        print("Llama 3:", response)
        # Start speaking
        player = speak(response)
        # Start listening for interrupt in a thread
        interrupt_event = threading.Event()
        interrupt_thread = threading.Thread(target=listen_for_interrupt, args=(interrupt_event,))
        interrupt_thread.start()
        # Wait for speech to finish or for interrupt
        while player.poll() is None and not interrupt_event.is_set():
            pass
        # If interrupted, stop speaking
        if interrupt_event.is_set():
            stop_speaking(player)
            print("Speech interrupted by user.")
        # Wait for the interrupt thread to finish
        interrupt_thread.join()

if __name__ == "__main__":
    main()