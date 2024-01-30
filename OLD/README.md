# Transcription App

A Python-based transcription application with a user-friendly interface, leveraging the power of PyQt6 for GUI development and Deepgram for accurate and efficient speech-to-text conversion.

## Features

- **Audio Recording**: Record audio directly within the application using the selected microphone.
- **Live Transcription**: Transcribe audio in real-time using Deepgram's advanced speech recognition technology.
- **File-Based Transcription**: Import audio files for transcription, supporting various formats like MP3 and WAV.
- **Dynamic Interface**: Responsive GUI with interactive elements such as dynamic buttons displayed on hover in the QListWidget.
- **Microphone Selection**: Choose from available microphones connected to your system.
- **Language Selection**: Supports multiple languages for transcription, easily switchable through the interface.
- **User-Friendly Layout**: Intuitive and clean interface layout, suitable for both novice and experienced users.

## Requirements

- Python 3.6 or higher
- PyQt6
- sounddevice
- Deepgram API Key
- pyaudio
- speech_recognition

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-github-username/transcription-app.git
    ```
2. Navigate to the project directory:
    ```bash
    cd transcription-app
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Launch the application:
    ```bash
    python main.py
    ```
2. Select your microphone and preferred language for transcription.
3. Click the "Record" button to start recording and transcribing.
4. Import audio files using the "Import" button if needed.
5. Transcriptions are displayed in the text browser and saved in the designated directory.

## Contributing

Contributions to enhance the application are welcome. Please follow the standard GitHub workflow - fork, clone, branch, commit, and pull request.

## License

This project is licensed under the MIT License. Please see the LICENSE file for more details.

## Acknowledgments

Special thanks to the developers and contributors of PyQt6, Deepgram, and other dependencies used in this project.

---

Developed with ❤️ by [Your Name or GitHub Username]
