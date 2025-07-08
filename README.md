# AI Voice Assistant 🎤🤖

A Python-based AI voice assistant that can play music, answer questions using Llama 3, and respond to voice commands. Perfect for beginners who want to explore AI and voice recognition technology!

## 🌟 Features

- **Voice Recognition**: Listen and respond to voice commands
- **Music Player**: Play songs from your music library with voice commands
- **AI Chat**: Get answers to questions using Llama 3 AI model
- **Text-to-Speech**: Hear responses spoken back to you
- **Wake Word Detection**: Activate with custom wake words
- **Music Database**: Manage your music collection easily

## 📋 Prerequisites

Before you start, make sure you have:

1. **Python 3.8 or higher** installed on your computer
2. **Git** installed (to download the project)
3. **Microphone** connected to your computer
4. **Speakers or headphones** for audio output
5. **Internet connection** (for speech recognition and AI responses)

### How to Check Your Python Version

Open your terminal/command prompt and type:
```bash
python --version
```
or
```bash
python3 --version
```

If you don't have Python installed, download it from [python.org](https://python.org).

## 🚀 Installation Guide

### Step 1: Download the Project

1. Open your terminal/command prompt
2. Navigate to where you want to store the project:
   ```bash
   cd /path/to/your/desired/location
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-voice-assistant.git
   ```
4. Enter the project folder:
   ```bash
   cd ai-voice-assistant
   ```

### Step 2: Create a Virtual Environment

A virtual environment keeps your project dependencies separate from other Python projects.

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You'll know it's activated when you see `(venv)` at the beginning of your command line.

### Step 3: Install Required Packages

With your virtual environment activated, install the required packages:

```bash
pip install pvporcupine pyaudio speechrecognition requests gtts
```

**Note**: If you get an error installing `pyaudio`, you might need to install additional system dependencies:

**On macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install python3-pyaudio portaudio19-dev
pip install pyaudio
```

**On Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

### Step 4: Set Up Porcupine (Wake Word Detection)

1. Go to [Picovoice Console](https://console.picovoice.ai/)
2. Create a free account
3. Get your Access Key
4. Open the file `bloom_music_voice_assistant.py`
5. Find the line that says `ACCESS_KEY = ""`
6. Replace the empty quotes with your access key:
   ```python
   ACCESS_KEY = "your_access_key_here"
   ```

### Step 5: Set Up Llama 3 (Optional - for AI responses)

If you want the AI chat feature:

1. Install [Ollama](https://ollama.ai/) on your computer
2. Download the Llama 3 model:
   ```bash
   ollama pull llama3
   ```
3. Start Ollama:
   ```bash
   ollama serve
   ```

## 🎵 Adding Music to Your Assistant

### Step 1: Prepare Your Music Files

1. Create a folder called `Music` in your project directory
2. Add your MP3 files to this folder
3. Make sure the files are named clearly (e.g., "song_name.mp3")

### Step 2: Add Songs to the Database

Run the assistant and use voice commands like:
- "Add song [song name] to database"
- "Add [artist name] [song title] to database"

Or manually edit the `music_database.json` file:
```json
{
    "song_key": {
        "title": "Song Title",
        "artist": "Artist Name",
        "file_path": "Music/song_file.mp3"
    }
}
```

## 🎮 How to Use

### Basic Voice Assistant

1. Make sure your virtual environment is activated
2. Run the basic voice assistant:
   ```bash
   python voice_assistant.py
   ```
3. Speak your questions or commands
4. Say "stop", "exit", or "quit" to end the program

### Music Voice Assistant (Recommended)

1. Make sure your virtual environment is activated
2. Run the music assistant:
   ```bash
   python bloom_music_voice_assistant.py
   ```
3. Use voice commands like:
   - "Play [song name]"
   - "Stop music"
   - "What songs do you have?"
   - "Add [song name] to database"
   - "Remove [song name] from database"

## 🗣️ Voice Commands

### Music Commands
- **"Play [song name]"** - Play a specific song
- **"Stop music"** - Stop currently playing music
- **"What songs do you have?"** - List all available songs
- **"Add [song name] to database"** - Add a new song
- **"Remove [song name] from database"** - Remove a song

### General Commands
- **"What's the weather?"** - Get weather information
- **"Tell me a joke"** - Hear a random joke
- **"What time is it?"** - Get current time
- **"Stop" / "Exit" / "Quit"** - End the program

### AI Chat Commands
- **"Ask [your question]"** - Get AI-powered answers
- **"What is [topic]?"** - Learn about any topic
- **"How do I [task]?"** - Get step-by-step instructions

## 🔧 Troubleshooting

### Common Issues and Solutions

**1. "No module named 'pyaudio'"**
- Make sure you're in your virtual environment
- Reinstall pyaudio: `pip install pyaudio`

**2. "Microphone not found"**
- Check your microphone is connected and working
- Make sure your system allows microphone access
- Try a different microphone

**3. "Speech recognition not working"**
- Check your internet connection
- Speak clearly and slowly
- Try in a quieter environment

**4. "Music won't play"**
- Check if the music file exists in the correct path
- Make sure the file is a valid MP3
- Try installing additional audio players:
  ```bash
  # On macOS
  brew install mpg123
  
  # On Ubuntu/Debian
  sudo apt-get install mpg123
  ```

**5. "Ollama connection error"**
- Make sure Ollama is running: `ollama serve`
- Check if Llama 3 is installed: `ollama list`
- Verify the model name in the code matches your installed model

### Getting Help

If you're still having issues:

1. Check the error messages in your terminal
2. Make sure all prerequisites are installed
3. Verify your virtual environment is activated
4. Try running the basic voice assistant first: `python voice_assistant.py`

## 📁 Project Structure

```
ai-voice-assistant/
├── README.md                    # This file
├── voice_assistant.py           # Basic voice assistant
├── bloom_music_voice_assistant.py  # Full music assistant
├── music_player.py              # Music player functions
├── voice_assistant_song.py      # Song-specific assistant
├── music_database.json          # Your music library
├── Music/                       # Your music files folder
├── venv/                        # Virtual environment (created during setup)
└── response.mp3                 # Temporary audio file
```

## 🎯 Next Steps

Once you're comfortable with the basics:

1. **Customize Wake Words**: Create your own wake word in Picovoice Console
2. **Add More Features**: Extend the assistant with new commands
3. **Improve AI Responses**: Fine-tune the Llama 3 model
4. **Add Voice Commands**: Create custom voice commands for your needs
5. **Integrate with Smart Home**: Connect to smart devices

## 🤝 Contributing

Found a bug or want to add a feature? 

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use, modify, and distribute!

## 🙏 Acknowledgments

- [Picovoice](https://picovoice.ai/) for wake word detection
- [Ollama](https://ollama.ai/) for local AI models
- [Google Speech Recognition](https://cloud.google.com/speech-to-text) for voice recognition
- [gTTS](https://gtts.readthedocs.io/) for text-to-speech

---

**Happy coding! 🎉**

If you found this helpful, please give it a ⭐ on GitHub! # AI-Voice-Assistant-with-Music-Player
