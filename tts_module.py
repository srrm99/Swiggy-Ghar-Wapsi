import os
import base64
import wave
import io
import requests
import re
from dotenv import load_dotenv
import sounddevice as sd
import soundfile as sf # For reading audio data for playback

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
TTS_CHARACTER_LIMIT = 1500 # As per Sarvam API documentation
MIN_TEXT_LENGTH_FOR_FORCED_TWO_WAY_SPLIT = 20 # Chars, don't split very short texts forcibly

# Placeholder for silent audio (approx 0.1s of silence, 16kHz, mono, 16-bit PCM WAV)
# This can be used if TTS fails for an empty string after cleaning or for error handling.
SILENT_WAV_BASE64 = "UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQQAAAAAAA=="


def _clean_text_for_tts(text_input):
    """Cleans text by removing common markdown, conversational prefixes, and emojis."""
    if not text_input:
        return ""

    # Remove conversational prefixes like "You:", "Bot:", "Assistant:", etc. and leading/trailing quotes
    cleaned_text = re.sub(r'^\w+:\s*', '', text_input.strip()).strip('\'"')

    cleaned_text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', cleaned_text)
    cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_text)
    cleaned_text = re.sub(r'\*(.*?)\*', r'\1', cleaned_text)
    cleaned_text = re.sub(r'^#+\s*', '', cleaned_text, flags=re.MULTILINE)

    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"
                               u"\U0001F300-\U0001F5FF"
                               u"\U0001F680-\U0001F6FF"
                               u"\U0001F1E0-\U0001F1FF"
                               u"\u2600-\u26FF"
                               u"\u2700-\u27BF"
                               u"\uFE0F"
                               u"\U0001F900-\U0001F9FF"
                               "]+", flags=re.UNICODE)
    cleaned_text = emoji_pattern.sub(r'', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    cleaned_text = cleaned_text.replace('```', '')
    
    cleaned_text = cleaned_text.strip()

    return cleaned_text

def _call_sarvam_tts(text_chunk, lang_code, speaker='meera', model='bulbul:v1'):
    """Helper function to call Sarvam TTS API for a single text chunk."""
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY not found for TTS call.")
    if not text_chunk or not text_chunk.strip():
        return SILENT_WAV_BASE64

    headers = {
        'api-subscription-key': SARVAM_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': text_chunk,
        'target_language_code': lang_code, # e.g., "hi-IN"
        'speaker': speaker, # e.g., "meera" for bulbul:v1
        'model': model 
    }

    response = requests.post('https://api.sarvam.ai/text-to-speech', json=payload, headers=headers)

    if not response.ok:
        error_msg = f"Sarvam TTS API request failed for chunk with status {response.status_code}: {response.text}"
        raise Exception(error_msg)
    
    json_response = response.json()
    if not json_response.get('audios') or not json_response['audios'][0]:
        error_msg = "Sarvam TTS API response OK, but no audio data found in 'audios' list."
        return SILENT_WAV_BASE64
    
    base64_audio_for_chunk = json_response['audios'][0]
    
    if not base64_audio_for_chunk or len(base64_audio_for_chunk) < 100:
        return SILENT_WAV_BASE64
        
    return base64_audio_for_chunk

def _chunk_text_boundary_aware(text, max_length):
    """Chunks text, trying to respect sentence/word boundaries."""
    chunks = []
    current_pos = 0
    text_len = len(text)

    while current_pos < text_len:
        if text_len - current_pos <= max_length:
            chunks.append(text[current_pos:])
            break
        
        split_at = current_pos + max_length
        best_split_point = split_at 

        sentence_delimiters = ['. ', '! ', '? ', '\n'] 
        found_sentence_split = -1
        for delim in sentence_delimiters:
            last_occurrence = text.rfind(delim, current_pos, split_at)
            if last_occurrence != -1:
                potential_split = last_occurrence + len(delim)
                if potential_split > found_sentence_split:
                    found_sentence_split = potential_split
        
        if found_sentence_split > current_pos: 
            best_split_point = found_sentence_split
        else:
            last_space = text.rfind(' ', current_pos, split_at)
            if last_space > current_pos: 
                best_split_point = last_space + 1
        
        chunk = text[current_pos:best_split_point]
        chunks.append(chunk)
        current_pos = best_split_point

    final_chunks = [c.strip() for c in chunks if c.strip()]
    return final_chunks

def _concatenate_wav_from_base64_list(base64_audio_list):
    """Decodes list of base64 WAV audio, concatenates them, and re-encodes to base64."""
    if not base64_audio_list:
        return SILENT_WAV_BASE64
    if len(base64_audio_list) == 1:
        return base64_audio_list[0]

    all_frames_data = []
    wav_params = None

    for i, b64_string in enumerate(base64_audio_list):
        if not b64_string or b64_string == SILENT_WAV_BASE64: # Skip if it's our placeholder for silence
            continue
        try:
            wav_bytes = base64.b64decode(b64_string)
            with io.BytesIO(wav_bytes) as wav_file_in_memory:
                with wave.open(wav_file_in_memory, 'rb') as wf:
                    current_params = wf.getparams()
                    if not all_frames_data: # First valid audio chunk
                        wav_params = current_params
                    elif wav_params[:3] != current_params[:3]: 
                        continue # Skip this chunk to avoid corruption
                    
                    frames = wf.readframes(wf.getnframes())
                    all_frames_data.append(frames)
        except Exception as e:
            # Continue to next chunk, hoping others are fine
            pass
    
    if not all_frames_data or not wav_params:
        return SILENT_WAV_BASE64

    with io.BytesIO() as wav_output_in_memory:
        with wave.open(wav_output_in_memory, 'wb') as wf_out:
            wf_out.setparams(wav_params)
            for frame_data_chunk in all_frames_data:
                wf_out.writeframes(frame_data_chunk)
        concatenated_wav_bytes = wav_output_in_memory.getvalue()
    
    final_concatenated_base64 = base64.b64encode(concatenated_wav_bytes).decode('utf-8')
    return final_concatenated_base64

def text_to_speech(text, lang_code="hi-IN", speaker='meera', model='bulbul:v1'):
    """
    Converts text to speech. Handles chunking and returns a single base64 encoded WAV string.
    Defaults are set for a Hindi conversation.
    """
    cleaned_text = _clean_text_for_tts(text)
    if not cleaned_text:
        return SILENT_WAV_BASE64
    
    text_chunks = _chunk_text_boundary_aware(cleaned_text, TTS_CHARACTER_LIMIT)
    if not text_chunks:
        return SILENT_WAV_BASE64

    base64_audio_parts = []
    for chunk in text_chunks:
        try:
            base64_audio_chunk = _call_sarvam_tts(chunk, lang_code, speaker, model)
            base64_audio_parts.append(base64_audio_chunk)
        except Exception as e:
            print(f"TTS Error: {e}")
            base64_audio_parts.append(SILENT_WAV_BASE64)

    return _concatenate_wav_from_base64_list(base64_audio_parts)

def play_audio_from_base64(base64_audio_string):
    """Decodes base64 WAV audio and plays it using sounddevice."""
    if not base64_audio_string:
        return
    if base64_audio_string == SILENT_WAV_BASE64:
        return

    try:
        wav_bytes = base64.b64decode(base64_audio_string)
        with io.BytesIO(wav_bytes) as wav_file_in_memory:
            data, samplerate = sf.read(wav_file_in_memory)
        sd.play(data, samplerate)
        sd.wait() # Wait until playback is finished
    except Exception as e:
        print(f"Error playing audio: {e}")

# --- Example Usage (can be run directly) ---
if __name__ == "__main__":
    print("TTS Module - Interactive Test")
    print("=============================")
    
    test_text_hindi = "नमस्ते! यह वाणी संश्लेषण सेवा का परीक्षण है।"
    
    try:
        print(f"\nSynthesizing Hindi: '{test_text_hindi}'")
        # Now uses the updated defaults
        base64_output_hindi = text_to_speech(test_text_hindi)
        if base64_output_hindi and base64_output_hindi != SILENT_WAV_BASE64:
            print(f"Hindi TTS successful. Playing audio...")
            play_audio_from_base64(base64_output_hindi)
        else:
            print("Hindi TTS failed or produced silent audio.")

    except Exception as e:
        print(f"An unexpected error occurred during TTS test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTTS Test finished.") 