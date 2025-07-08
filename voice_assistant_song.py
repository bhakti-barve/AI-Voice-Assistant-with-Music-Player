import pvporcupine
import pyaudio
import struct
import speech_recognition as sr
import requests
from gtts import gTTS
import subprocess
import threading
import time
import os
import signal
import tempfile

# Replace with your Porcupine AccessKey
ACCESS_KEY = ""


CUSTOM_WAKEWORD_PATH = "" 

# ===== FUNCTIONS =====
def speak(text):
    """Speak text using gTTS and afplay (interruptible) - no file saving"""
    try:
        # Create a temporary file that will be automatically deleted
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name
            
        # Generate speech file
        tts = gTTS(text=text, lang='en')
        tts.save(temp_filename)
        
        # Play with afplay (macOS)
        player = subprocess.Popen(["afplay", temp_filename])
        
        # Return both player and filename for cleanup
        return player, temp_filename
    except Exception as e:
        print(f"TTS Error: {e}")
        return None, None

def stop_speaking(player, temp_filename=None):
    """Stop the speech playback and clean up temporary file"""
    if player and player.poll() is None:
        try:
            os.kill(player.pid, signal.SIGTERM)
            print("Speech stopped.")
        except Exception as e:
            print(f"Error stopping speech: {e}")
    
    # Clean up temporary file
    if temp_filename and os.path.exists(temp_filename):
        try:
            os.remove(temp_filename)
        except Exception as e:
            print(f"Error removing temporary file: {e}")

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
        print(f"Sending to Llama 3: {prompt}")
        response = requests.post(url, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            json_data = response.json()
            result = json_data.get("response") or json_data.get("message") or "No valid response from Llama 3."
            print(f"Llama 3 result: {result}")
            return result
        else:
            return f"Sorry, I couldn't get a response from Llama 3. Status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Make sure it's running with 'ollama serve' or 'ollama run llama3'."
    except requests.exceptions.Timeout:
        return "Error: Request to Ollama timed out. The model might be loading."
    except Exception as e:
        print(f"Llama 3 communication error: {e}")
        return f"Error communicating with Llama 3: {e}"

def listen_with_retry(prompt="Listening...", max_retries=3):
    """Listen for command with retry mechanism"""
    r = sr.Recognizer()
    
    # Optimize microphone settings
    r.energy_threshold = 3000
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8
    
    for attempt in range(max_retries):
        try:
            with sr.Microphone() as source:
                print(f"{prompt} (Attempt {attempt + 1}/{max_retries})")
                
                # Adjust for ambient noise
                print("Adjusting for ambient noise...")
                r.adjust_for_ambient_noise(source, duration=0.5)
                print("Ready to listen!")
                
                audio = r.listen(source, timeout=8, phrase_time_limit=8)
                print("Audio captured, processing...")
                
                command = r.recognize_google(audio)
                print(f"You said: {command}")
                return command.lower()
                
        except sr.WaitTimeoutError:
            print(f"Attempt {attempt + 1}: No speech detected, trying again...")
            continue
        except sr.UnknownValueError:
            print(f"Attempt {attempt + 1}: Could not understand speech, trying again...")
            continue
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error: {e}")
            continue
    
    print("Failed to capture command after all attempts.")
    return ""

def listen_for_interrupt():
    """Listen for interrupt command while speech is playing"""
    r = sr.Recognizer()
    r.energy_threshold = 3000
    
    with sr.Microphone() as source:
        while True:
            try:
                print("Say 'stop' to interrupt...")
                audio = r.listen(source, timeout=2, phrase_time_limit=2)
                command = r.recognize_google(audio).lower()
                print(f"Interrupt heard: {command}")
                if any(word in command for word in ["stop", "exit", "quit"]):
                    return True
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print(f"Interrupt listening error: {e}")
                continue

def speak_with_interrupt(text):
    """Speak text and allow interruption - no file saving"""
    print("Speaking response...")
    
    # Start speaking with temporary file
    player, temp_filename = speak(text)
    if player is None:
        return False
    
    # Start listening for interrupt in a separate thread
    interrupt_event = threading.Event()
    interrupt_thread = threading.Thread(target=lambda: interrupt_event.set() if listen_for_interrupt() else None)
    interrupt_thread.daemon = True
    interrupt_thread.start()
    
    # Wait for speech to finish or interrupt
    while player.poll() is None and not interrupt_event.is_set():
        time.sleep(0.1)
    
    # If interrupted, stop the speech
    if interrupt_event.is_set():
        stop_speaking(player, temp_filename)
        return True
    else:
        # Clean up temporary file when speech completes normally
        stop_speaking(player, temp_filename)
        return False

def initialize_audio():
    """Initialize audio with error handling"""
    try:
        pa = pyaudio.PyAudio()
        
        # Try to find a working audio device
        device_count = pa.get_device_count()
        input_device = None
        
        for i in range(device_count):
            device_info = pa.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_device = i
                print(f"Using audio device: {device_info['name']}")
                break
        
        if input_device is None:
            print("No input device found!")
            return None, None
        
        # Create audio stream with specific device
        audio_stream = pa.open(
            rate=16000,  # Standard rate for speech recognition
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=input_device,
            frames_per_buffer=1024
        )
        
        print("Audio stream initialized successfully!")
        return pa, audio_stream
        
    except Exception as e:
        print(f"Audio initialization error: {e}")
        return None, None

def main():
    print("=== Voice Assistant with Custom 'Hi Bloom' Wake Word ===")
    print("Make sure Ollama is running with: ollama run llama3")
    print("No response files will be saved - using temporary files only")
    
    # Check if wake word file exists
    if not os.path.exists(CUSTOM_WAKEWORD_PATH):
        print(f"Error: Wake word file '{CUSTOM_WAKEWORD_PATH}' not found!")
        print("Please make sure the .ppn file is in the same directory as this script.")
        return
    
    # Initialize Porcupine with custom wake word
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[CUSTOM_WAKEWORD_PATH]
        )
        print("Porcupine initialized successfully!")
    except Exception as e:
        print(f"Error initializing Porcupine: {e}")
        print("Please check your AccessKey and wake word file.")
        return
    
    # Initialize audio
    pa, audio_stream = initialize_audio()
    if pa is None or audio_stream is None:
        print("Failed to initialize audio. Exiting.")
        return
    
    # Test TTS
    print("Testing speech synthesis...")
    test_player, test_filename = speak("Hello, I am your voice assistant. Say Hi Bloom to activate me.")
    if test_player:
        test_player.wait()
        stop_speaking(test_player, test_filename)
    
    print("Say 'Hi Bloom' to activate the assistant...")
    
    try:
        while True:
            # Read audio with error handling
            try:
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            except Exception as e:
                print(f"Audio read error: {e}")
                continue
            
            # Process with Porcupine
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                print("Wake word detected! Listening for your command...")
                wake_player, wake_filename = speak("Hi Bloom detected! What can I help you with?")
                if wake_player:
                    wake_player.wait()
                    stop_speaking(wake_player, wake_filename)
                
                # Wait a moment
                time.sleep(1)
                
                # Listen for command with retry mechanism
                command = listen_with_retry("What would you like to know?")
                
                if not command:
                    print("No command heard, going back to wake word...")
                    continue
                    
                if any(word in command for word in ["stop", "exit", "quit"]):
                    goodbye_player, goodbye_filename = speak("Goodbye!")
                    if goodbye_player:
                        goodbye_player.wait()
                        stop_speaking(goodbye_player, goodbye_filename)
                    break
                    
                print(f"Processing command: {command}")
                response = ask_llama3(command)
                
                # Speak with interrupt capability
                was_interrupted = speak_with_interrupt(response)
                
                if was_interrupted:
                    print("Response was interrupted.")
                else:
                    print("Response completed.")
                
                print("Say 'Hi Bloom' to activate again.")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        try:
            if audio_stream:
                audio_stream.stop_stream()
                audio_stream.close()
            if pa:
                pa.terminate()
            porcupine.delete()
        except Exception as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    main()