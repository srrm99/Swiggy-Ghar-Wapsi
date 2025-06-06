from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import json

from asr_module import speech_to_text
from llm_module import get_llm_response, get_json_summary
from tts_module import text_to_speech, SILENT_WAV_BASE64

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# In-memory store for conversation history (for simplicity)
# In a production app, you'd use a database or a more robust session management.
conversation_history = []

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_conversation():
    """
    Starts the conversation by prompting the LLM for a greeting,
    storing a valid initial history, and returning the audio.
    """
    global conversation_history
    
    # Prime the LLM to start the conversation.
    priming_history = [{"role": "user", "content": "Start the conversation by greeting me in Hindi and asking your first question."}]
    
    try:
        # Get the initial response from the LLM
        initial_llm_response = get_llm_response(priming_history)
        print(f"[app.py] Initial LLM Response: '{initial_llm_response}'")
        
        # Now, establish the official conversation history with the priming message and the bot's response.
        conversation_history = priming_history + [{"role": "assistant", "content": initial_llm_response}]
        
        audio_base64 = text_to_speech(initial_llm_response)

        if audio_base64 == SILENT_WAV_BASE64:
            print("[app.py] TTS module returned silent audio for the initial response.")
        
        return jsonify({
            "status": "success",
            "audio": audio_base64,
            "transcript": initial_llm_response
        })

    except Exception as e:
        print(f"Error in /start: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/respond', methods=['POST'])
def respond():
    """
    Handles subsequent turns in the conversation.
    """
    global conversation_history
    
    if 'audio_data' not in request.files:
        return jsonify({"status": "error", "message": "No audio file provided."}), 400

    audio_file = request.files['audio_data']
    audio_blob = audio_file.read()

    try:
        user_transcript = speech_to_text(audio_blob)
        if not user_transcript:
            return jsonify({
                "status": "success",
                "audio": None,
                "transcript": "[Silence Detected]"
            })

        conversation_history.append({"role": "user", "content": user_transcript})

        llm_response = get_llm_response(conversation_history)
        conversation_history.append({"role": "assistant", "content": llm_response})

        audio_base64 = text_to_speech(llm_response)
        
        return jsonify({
            "status": "success",
            "audio": audio_base64,
            "user_transcript": user_transcript,
            "bot_transcript": llm_response
        })

    except Exception as e:
        print(f"Error in /respond: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def format_transcript_for_summary(history):
    """Formats the conversation history for the JSON summary prompt."""
    transcript = ""
    # Skip the first priming message from the user
    for message in history[1:]:
        role = "bot" if message["role"] == "assistant" else "de"
        transcript += f'{role}: {message["content"]}\n'
    return transcript.strip()

@app.route('/summarize', methods=['POST'])
def summarize():
    """
    Summarizes the conversation and returns a JSON object.
    """
    global conversation_history
    if not conversation_history:
        return jsonify({"status": "error", "message": "No conversation to summarize."}), 400
        
    try:
        # Format the transcript for the summarizer
        transcript = format_transcript_for_summary(conversation_history)
        print(f"[app.py] Transcript for summarization:\n{transcript}")

        # Get the JSON summary
        summary_json_str = get_json_summary(transcript)
        print(f"[app.py] Received JSON summary string: {summary_json_str}")
        
        # Ensure the string is parsed into a JSON object before sending
        summary_json = json.loads(summary_json_str)

        return jsonify({"status": "success", "summary": summary_json})
    except Exception as e:
        print(f"Error in /summarize: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Check for the new OpenRouter API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("FATAL: OPENROUTER_API_KEY environment variable is not set.")
        print("Please create or update your .env file with your OpenRouter API key.")
    else:
        app.run(debug=True, port=5001) 