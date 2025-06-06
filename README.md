# Swiggy-Ghar-Wapsi

This project is a Flask-based web application that seems to be related to Swiggy and provides some insights about Delhi.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/srrm99/Swiggy-Ghar-Wapsi.git
    cd Swiggy-Ghar-Wapsi
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file and add your API keys:**
    ```
    OPENAI_API_KEY="your_openai_api_key"
    ```

## Running the application

1.  **Run the Flask application:**
    ```bash
    python app.py
    ```

2.  Open your browser and go to `http://127.0.0.1:5000`.

## How to test

1.  Navigate to the home page.
2.  Interact with the application to see the features.
    - There appears to be functionality for audio input and output (ASR and TTS).
    - There is also an LLM module, which might be used for generating text or insights. 