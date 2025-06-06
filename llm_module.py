from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Switched from Sarvam to OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
YOUR_SITE_URL = "http://localhost:5001" # Optional, for OpenRouter analytics
YOUR_SITE_NAME = "Hindi Voice Bot" # Optional, for OpenRouter analytics

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

def get_system_prompt(prompt_file="prompts/calling_prompt.md"):
    """Reads a system prompt from a specified file."""
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {prompt_file} not found.")
        return "You are a helpful assistant."

SYSTEM_PROMPT = get_system_prompt()

def get_llm_response(conversation_history):
    """
    Calls the OpenRouter API with the conversation history and gets a response from GPT-4o.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            model="openai/gpt-4o", # Using a common gpt-4o model
            messages=messages,
            temperature=0.7,
            top_p=0.9,
            stream=False
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"OpenRouter API request failed: {e}")
        # The OpenAI library's error messages are often descriptive enough.
        raise Exception(f"OpenRouter API request failed: {e}") from e

def get_json_summary(conversation_transcript):
    """
    Calls the OpenRouter API to get a JSON summary of a conversation.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

    json_system_prompt = get_system_prompt("prompts/json_prompt.md")
    
    # The conversation transcript is passed as a single user message
    messages = [
        {"role": "system", "content": json_system_prompt},
        {"role": "user", "content": conversation_transcript}
    ]

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            model="openai/gpt-4o",
            messages=messages,
            # For JSON output, it's good practice to ask the model to behave deterministically
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"OpenRouter API request for JSON summary failed: {e}")
        raise

if __name__ == '__main__':
    print("LLM Module Test (OpenRouter)")
    print("============================")
    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY is not set. Cannot run a live test.")
    else:
        print("OPENROUTER_API_KEY is set.")
        print("System Prompt:")
        print(SYSTEM_PROMPT)
        print("\n--- Running a test conversation ---")
        
        history = [{"role": "user", "content": "Start the conversation by greeting me in Hindi and asking your first question."}]
        
        try:
            print("Getting initial greeting from LLM...")
            initial_response = get_llm_response(history)
            print(f"LLM (start): {initial_response}")
            history.append({"role": "assistant", "content": initial_response})
            
            user_message = "मैं ठीक हूँ, धन्यवाद।"
            print(f"User: {user_message}")
            history.append({"role": "user", "content": user_message})

            print("Getting LLM response...")
            llm_reply = get_llm_response(history)
            print(f"LLM: {llm_reply}")

        except Exception as e:
            print(f"An error occurred during the test: {e}") 