import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydub import AudioSegment
import speech_recognition as sr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- FFmpeg setup ---

ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe")
ffprobe_path = os.path.join(os.getcwd(), "ffprobe.exe")

AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

print("🎬 FFmpeg converter path:", AudioSegment.converter)
print("🧩 FFprobe path:", AudioSegment.ffprobe)
print("FFmpeg exists?", os.path.exists(AudioSegment.converter))
print("FFprobe exists?", os.path.exists(AudioSegment.ffprobe))

# --- Flask setup ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

UPLOAD_FOLDER = "temp_audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return jsonify({"message": "Speech-to-Text backend is running!"})


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    original_filename = file.filename or "upload"
    file_path = os.path.join(UPLOAD_FOLDER, original_filename)
    file.save(file_path)
    print("📥 Saved incoming file:", file_path)
    print(f"📂 File exists after save? {os.path.exists(file_path)}")

    try:
        # --- Convert to WAV ---
        ext = original_filename.rsplit(".", 1)[-1].lower()
        print("🎧 Attempting conversion from:", ext)

        sound = AudioSegment.from_file(file_path, format=ext)
        wav_path = file_path.rsplit(".", 1)[0] + ".wav"
        sound.export(wav_path, format="wav")
        print("✅ Exported WAV to:", wav_path)

        # --- Speech Recognition ---
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            print("🎙️ Reading audio...")
            audio_data = recognizer.record(source)
            print("🤖 Recognizing speech...")
            text = recognizer.recognize_google(audio_data)
            print("📝 Transcript:", text)

        return jsonify({"transcript": text})

    except sr.UnknownValueError:
        print("❌ Speech not recognized")
        return jsonify({"error": "Speech not recognized"}), 400

    except FileNotFoundError as fnf:
        print("❌ File not found or conversion failed:", fnf)
        return jsonify({"error": f"File not found or conversion failed: {fnf}"}), 500

    except Exception as e:
        print("❌ Error during transcription:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        # --- Cleanup temporary files ---
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if "wav_path" in locals() and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception as cleanup_err:
            print("⚠️ Cleanup error:", cleanup_err)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
