import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydub import AudioSegment
import speech_recognition as sr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'temp_audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return jsonify({"message": "Speech-to-Text backend is running!"})

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Convert to WAV if necessary
    if not file.filename.endswith('.wav'):
        sound = AudioSegment.from_file(file_path)
        wav_path = file_path.rsplit('.', 1)[0] + '.wav'
        sound.export(wav_path, format='wav')
    else:
        wav_path = file_path

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            print("Transcript:", text)
            return jsonify({"transcript": text})

    except sr.UnknownValueError:
        return jsonify({"error": "Speech not recognized"}), 400
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary files
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
