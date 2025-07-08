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
import json
import urllib.parse

# ===== CONFIGURATION =====
# Replace with your Porcupine AccessKey
ACCESS_KEY = ""
CUSTOM_WAKEWORD_PATH = ""
MUSIC_DATABASE_FILE = "music_database.json"

# ===== FUNCTIONS =====
def load_music_database():
    """Load music database from JSON file"""
    try:
        if os.path.exists(MUSIC_DATABASE_FILE):
            with open(MUSIC_DATABASE_FILE, 'r') as file:
                database = json.load(file)
            print(f"Loaded {len(database)} songs from database.")
            return database
        else:
            print(f"Music database file '{MUSIC_DATABASE_FILE}' not found. Creating empty database.")
            return {}
    except Exception as e:
        print(f"Error loading music database: {e}")
        return {}

def save_music_database(database):
    """Save music database to JSON file"""
    try:
        with open(MUSIC_DATABASE_FILE, 'w') as file:
            json.dump(database, file, indent=4)
        print("Music database saved successfully.")
    except Exception as e:
        print(f"Error saving music database: {e}")

def add_song_to_database(song_name, title, artist, file_path):
    """Add a new song to the database"""
    database = load_music_database()
    database[song_name.lower()] = {
        "title": title,
        "artist": artist,
        "file_path": file_path
    }
    save_music_database(database)
    print(f"Added '{title}' to database.")

def remove_song_from_database(song_name):
    """Remove a song from the database"""
    database = load_music_database()
    if song_name.lower() in database:
        removed_song = database.pop(song_name.lower())
        save_music_database(database)
        print(f"Removed '{removed_song['title']}' from database.")
        return True
    else:
        print(f"Song '{song_name}' not found in database.")
        return False

def list_available_songs():
    """List all available songs in the database"""
    database = load_music_database()
    if not database:
        return "No songs in database."
    
    song_list = []
    for key, song_info in database.items():
        song_list.append(f"{song_info['title']} by {song_info['artist']}")
    
    return "Available songs: " + ", ".join(song_list)

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

def search_song(song_name):
    """Search for a song in the database"""
    database = load_music_database()
    song_name_lower = song_name.lower().strip()
    
    # Direct match
    if song_name_lower in database:
        return database[song_name_lower]
    
    # Partial match
    for key, song_info in database.items():
        if song_name_lower in key or key in song_name_lower:
            return song_info
    
    # Search in title and artist
    for key, song_info in database.items():
        if (song_name_lower in song_info["title"].lower() or 
            song_name_lower in song_info["artist"].lower()):
            return song_info
    
    return None

def play_song(song_name):
    """Play a song from the database with better error handling"""
    song_info = search_song(song_name)
    
    if song_info is None:
        return False, "Song is not available in the database."
    
    # Check if file exists
    if not os.path.exists(song_info["file_path"]):
        return False, f"Song file not found: {song_info['title']}"
    
    try:
        # Try different audio players in order of preference
        players_to_try = [
            ["afplay", song_info["file_path"]],
            ["mpg123", song_info["file_path"]],
            ["ffplay", "-nodisp", "-autoexit", song_info["file_path"]]
        ]
        
        player = None
        for player_cmd in players_to_try:
            try:
                print(f"Trying player: {player_cmd[0]}")
                player = subprocess.Popen(player_cmd, 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
                
                # Wait a moment to see if it starts successfully
                time.sleep(0.5)
                
                if player.poll() is None:
                    print(f"Successfully started with {player_cmd[0]}")
                    break
                else:
                    player = None
                    
            except FileNotFoundError:
                print(f"{player_cmd[0]} not available")
                continue
            except Exception as e:
                print(f"Error with {player_cmd[0]}: {e}")
                continue
        
        if player is None:
            return False, f"Could not play {song_info['title']} with any available player"
        
        return True, player, f"Now playing: {song_info['title']} by {song_info['artist']}"
        
    except Exception as e:
        return False, f"Error playing song: {e}"

def stop_music(player=None):
    """Stop music playback"""
    if player and player.poll() is None:
        try:
            os.kill(player.pid, signal.SIGTERM)
            print("Music stopped.")
            return True
        except Exception as e:
            print(f"Error stopping music: {e}")
            return False
    return False

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
    """Initialize audio with error handling and device selection"""
    try:
        pa = pyaudio.PyAudio()
        
        # List all available devices
        device_count = pa.get_device_count()
        print(f"Found {device_count} audio devices:")
        
        input_devices = []
        for i in range(device_count):
            try:
                device_info = pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append((i, device_info))
                    print(f"  {i}: {device_info['name']} (Input channels: {device_info['maxInputChannels']})")
            except Exception as e:
                print(f"  {i}: Error getting device info: {e}")
        
        if not input_devices:
            print("No input devices found!")
            return None, None
        
        # Try to find a working device
        working_device = None
        
        # First, try to find a device that's not iPhone Microphone
        for device_id, device_info in input_devices:
            if 'iphone' not in device_info['name'].lower():
                try:
                    # Test this device
                    test_stream = pa.open(
                        rate=16000,
                        channels=1,
                        format=pyaudio.paInt16,
                        input=True,
                        input_device_index=device_id,
                        frames_per_buffer=1024
                    )
                    test_stream.close()
                    working_device = device_id
                    print(f"Selected device: {device_info['name']}")
                    break
                except Exception as e:
                    print(f"Device {device_info['name']} failed: {e}")
                    continue
        
        # If no non-iPhone device works, try iPhone device
        if working_device is None:
            for device_id, device_info in input_devices:
                try:
                    test_stream = pa.open(
                        rate=16000,
                        channels=1,
                        format=pyaudio.paInt16,
                        input=True,
                        input_device_index=device_id,
                        frames_per_buffer=1024
                    )
                    test_stream.close()
                    working_device = device_id
                    print(f"Selected device: {device_info['name']}")
                    break
                except Exception as e:
                    print(f"Device {device_info['name']} failed: {e}")
                    continue
        
        if working_device is None:
            print("No working input device found!")
            return None, None
        
        # Create the actual audio stream
        audio_stream = pa.open(
            rate=16000,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=working_device,
            frames_per_buffer=1024
        )
        
        print("Audio stream initialized successfully!")
        return pa, audio_stream
        
    except Exception as e:
        print(f"Audio initialization error: {e}")
        return None, None

def process_command(command):
    """Process user commands including music requests - FIXED VERSION with better music control"""
    command_lower = command.lower()
    
    # Check for music commands
    if command_lower.startswith("play "):
        song_name = command_lower[5:].strip()  # Remove "play " from the beginning
        print(f"Searching for song: {song_name}")
        
        result = play_song(song_name)
        
        # Handle the return value properly
        if isinstance(result, tuple) and len(result) == 3:
            # Success case: (True, player, message)
            success, player, message = result
            print(message)
            
            # Speak the confirmation
            speak_with_interrupt(message)
            
            # Listen for stop command while music is playing - IMPROVED VERSION
            print("Say 'stop music' to stop the song...")
            r = sr.Recognizer()
            r.energy_threshold = 3000  # Lower threshold for better detection
            
            with sr.Microphone() as source:
                # Adjust for ambient noise
                r.adjust_for_ambient_noise(source, duration=0.5)
                
                while player.poll() is None:  # While music is playing
                    try:
                        print("Listening for stop command...")
                        audio = r.listen(source, timeout=3, phrase_time_limit=3)
                        stop_command = r.recognize_google(audio).lower()
                        print(f"Heard: {stop_command}")
                        
                        if any(phrase in stop_command for phrase in ["stop music", "stop song", "pause music", "stop"]):
                            print("Stop command detected!")
                            stop_music(player)
                            speak_with_interrupt("Music stopped.")
                            return True
                            
                    except sr.WaitTimeoutError:
                        # No speech detected, continue listening
                        continue
                    except sr.UnknownValueError:
                        # Could not understand speech, continue listening
                        continue
                    except Exception as e:
                        print(f"Error listening for stop command: {e}")
                        continue
            
            return True  # Command was handled
        
        elif isinstance(result, tuple) and len(result) == 2:
            # Error case: (False, error_message)
            success, error_message = result
            print(error_message)
            speak_with_interrupt(error_message)
            return True  # Command was handled
        
        else:
            # Unexpected return format
            print("Unexpected return format from play_song")
            return True  # Command was handled
    
    # Check for music management commands
    elif command_lower.startswith("add song "):
        # Format: "add song song_name|title|artist|file_path"
        parts = command_lower[9:].split("|")
        if len(parts) == 4:
            song_name, title, artist, file_path = parts
            add_song_to_database(song_name.strip(), title.strip(), artist.strip(), file_path.strip())
            speak_with_interrupt(f"Added {title} to database.")
        else:
            speak_with_interrupt("Please use format: add song song_name|title|artist|file_path")
        return True
    
    elif command_lower.startswith("remove song "):
        song_name = command_lower[12:].strip()
        if remove_song_from_database(song_name):
            speak_with_interrupt(f"Removed {song_name} from database.")
        else:
            speak_with_interrupt(f"Song {song_name} not found in database.")
        return True
    
    elif "list songs" in command_lower or "show songs" in command_lower:
        song_list = list_available_songs()
        speak_with_interrupt(song_list)
        return True
    
    # Check for stop music commands
    elif any(phrase in command_lower for phrase in ["stop music", "stop song", "pause music"]):
        # This would need to be handled globally if music is playing
        speak_with_interrupt("No music is currently playing.")
        return True  # Command was handled
    
    # For all other commands, use Llama 3
    return False

def main():
    print("=== Voice Assistant with Custom 'Hi Bloom' Wake Word ===")
    print("Make sure Ollama is running with: ollama run llama3")
    print("No response files will be saved - using temporary files only")
    print("Music feature: Say 'play [song name]' to play music")
    print("Database management: 'add song', 'remove song', 'list songs'")
    
    # Load music database
    music_db = load_music_database()
    print(f"Loaded {len(music_db)} songs from database.")
    
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
    
    # Initialize audio with better error handling
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
                
                # Process command (check for music first, then Llama 3)
                command_handled = process_command(command)
                
                if not command_handled:
                    # If not a music command, use Llama 3
                    print(f"Processing command with Llama 3: {command}")
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