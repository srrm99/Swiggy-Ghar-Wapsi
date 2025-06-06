import requests
import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

def speech_to_text(audio_blob):
    """
    Sends audio data to Sarvam ASR API and returns the transcript.
    """
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY not found in environment variables.")

    files = {'file': ('input.wav', audio_blob, 'audio/wav')}
    # Per docs, 'unknown' is best for saarika:v2 to auto-detect language.
    # The default model is saarika:v2, so it's not explicitly needed.
    data = {
        'language_code': 'unknown'
    }
    headers = {'api-subscription-key': SARVAM_API_KEY}

    try:
        response = requests.post('https://api.sarvam.ai/speech-to-text', files=files, data=data, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        return response.json().get("transcript")
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            print(f"ASR API Error Response: {e.response.text}")
        print(f"ASR API request failed: {e}")
        raise Exception(f"ASR API request failed: {e}") from e

if __name__ == '__main__':
    # This is a dummy example. To test this properly, you'd need an actual audio file.
    print("ASR Module Test")
    print("===============")
    if not SARVAM_API_KEY:
        print("SARVAM_API_KEY is not set. Cannot run a live test.")
    else:
        print("SARVAM_API_KEY is set.")
        print("To test, you would need a sample Hindi audio file (e.g., 'test_audio.wav').")
        # Example of how you would call it:
        # try:
        #     with open("test_audio.wav", "rb") as f:
        #         audio_data = f.read()
        #         transcript = speech_to_text(audio_data)
        #         print(f"Transcript: {transcript}")
        # except FileNotFoundError:
        #     print("Create a 'test_audio.wav' file with some Hindi speech to test the ASR module.")
        # except Exception as e:
        #     print(f"An error occurred during test: {e}") 