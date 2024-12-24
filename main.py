from dotenv import load_dotenv
import google.generativeai as genai
# import assemblyai as aai
import os
from flask import Flask, request, jsonify, send_from_directory
from pydub import AudioSegment
from flask_cors import CORS
from pyngrok import ngrok

load_dotenv()
app = Flask(__name__)
CORS(app)

gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

# assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
# aai.settings.api_key = assemblyai_key

# model = genai.GenerativeModel("gemini-1.5-flash")
# sample_audio = genai.upload_file("fire.mp3")
# response = model.generate_content(["Generate audio diarization for this interview. Use JSON format for the output, with the following keys: \"speaker\", \"transcription\". If you can infer the speaker, please do. If not, use speaker A, speaker B, etc.", sample_audio])
# print(response.text)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return send_from_directory(".","index.html")

@app.route("/upload", methods=["POST"])
def upload_audio():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400

        audio_file = request.files["audio"]
        webm_path = os.path.join(UPLOAD_FOLDER, "audio.webm")
        audio_file.save(webm_path)

        mp3_path = os.path.join(UPLOAD_FOLDER, "audio.mp3")
        audio = AudioSegment.from_file(webm_path, format="webm")
        audio.export(mp3_path, format="mp3")

        os.remove(webm_path)

        model = genai.GenerativeModel("gemini-1.5-flash")
        sample_audio = genai.upload_file(mp3_path)
        # speech_generation = speech_model.transcribe(mp3_path)
        response = model.generate_content(["Generate audio diarization for this interview. Use JSON format for the output, with the following keys: \"speaker\", \"transcription\". If you can infer the speaker, please do. If not, use speaker A, speaker B, etc.", sample_audio])
        # speech_output = speech_generation['text']

        return jsonify({"transcript": response.text}), 200
    except Exception as e:
        return jsonify({"error": "Failed to process audio", "details": str(e)}), 500
    
@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        speech_output = data.get("transcript")
        if not speech_output:
            return jsonify({"error": "No transcript provided"}), 400
        
        # llm_output = (speech_output)
        model = genai.GenerativeModel(
            "gemini-1.5-flash", 
            system_instruction="You are a Dental Assistant, working in a dental clinic. You are responsible for listening to the doctor and creating meaningful documentation for the patient."
            )
        response = model.generate_content(speech_output)

        return jsonify({"llm_generation": response.text}), 200
    except Exception as e:
        return jsonify({"error": "Failed to generate response", "details": str(e)}), 500
    
if __name__ == "__main__":
    public_url = ngrok.connect(5000)
    print(f" * ngrok tunnel available at: {public_url}")
    app.run(port=5000, host="0.0.0.0")
