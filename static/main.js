document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const endBtn = document.getElementById('end-btn');
    const statusDiv = document.getElementById('status');
    const conversationLog = document.getElementById('conversation-log');
    const summaryContainer = document.getElementById('summary-container');
    const summaryOutput = document.getElementById('summary-output');

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let conversationStarted = false;
    let audioContext; // To handle autoplay policies

    // --- Core Functions ---

    async function startConversation() {
        // Create and resume AudioContext on the first user gesture
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
        }

        if (conversationStarted) return;
        conversationStarted = true;
        
        updateStatus('Starting conversation...');
        startBtn.disabled = true;
        startBtn.innerText = 'Starting...';
        
        try {
            const response = await fetch('/start', { method: 'POST' });
            const data = await response.json();

            if (data.status === 'success' && data.audio) {
                addLogEntry('Bot', data.transcript);
                endBtn.style.display = 'inline-block'; // Show the end button
                playAudio(data.audio, () => {
                    updateStatus('Bot has finished speaking. Press to record your reply.');
                    startBtn.innerText = 'Start Recording';
                    startBtn.disabled = false;
                    // From now on, the button toggles recording
                    startBtn.onclick = toggleRecording;
                });
            } else {
                handleError('Could not start conversation.');
            }
        } catch (error) {
            handleError('Error starting conversation.', error);
        }
    }
    
    async function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            await startRecording();
        }
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = sendAudioToServer;

            audioChunks = [];
            mediaRecorder.start();
            isRecording = true;
            updateStatus('Recording... Press to stop.');
            startBtn.innerText = 'Stop Recording';
            startBtn.classList.add('recording');
        } catch (error) {
            handleError('Could not access microphone.', error);
            updateStatus('Microphone access denied. Please allow microphone access.');
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            updateStatus('Processing your audio...');
            startBtn.innerText = 'Processing...';
            startBtn.classList.remove('recording');
            startBtn.disabled = true;
        }
    }

    async function sendAudioToServer() {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio_data', audioBlob, 'recording.wav');

        try {
            const response = await fetch('/respond', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.status === 'success') {
                if(data.user_transcript) {
                    addLogEntry('You', data.user_transcript);
                }
                if (data.bot_transcript && data.audio) {
                    addLogEntry('Bot', data.bot_transcript);
                    playAudio(data.audio, () => {
                        updateStatus('Bot has finished speaking. Press to record your reply.');
                        startBtn.innerText = 'Start Recording';
                        startBtn.disabled = false;
                    });
                } else {
                     // Handle case where there might be no bot response (e.g. silence detected)
                    updateStatus('No response needed. Press to record again.');
                    startBtn.innerText = 'Start Recording';
                    startBtn.disabled = false;
                }
            } else {
                handleError('Failed to get a response from the server.');
            }
        } catch (error) {
            handleError('Error sending audio to server.', error);
        }
    }

    function playAudio(base64Audio, onEndCallback) {
        // Check for silent audio placeholder before attempting to play
        if (!base64Audio || base64Audio.length < 200) {
            console.log("Skipping playback for silent or empty audio.");
            if (onEndCallback) onEndCallback();
            return;
        }

        try {
            const audioSrc = `data:audio/wav;base64,${base64Audio}`;
            const audio = new Audio(audioSrc);
            updateStatus('Bot is speaking...');
            
            audio.onended = () => {
                if (onEndCallback) {
                    onEndCallback();
                }
            };
            
            audio.play().catch(e => {
                console.error("Audio playback failed:", e);
                updateStatus('Could not play audio. Please interact with the page first.');
                if (onEndCallback) onEndCallback();
            });
        } catch(e) {
            handleError("Error playing audio", e);
            if (onEndCallback) onEndCallback();
        }
    }

    async function summarizeConversation() {
        updateStatus('Summarizing conversation...');
        startBtn.disabled = true;
        endBtn.disabled = true;

        try {
            const response = await fetch('/summarize', { method: 'POST' });
            const data = await response.json();

            if (data.status === 'success' && data.summary) {
                updateStatus('Conversation ended and summarized.');
                summaryOutput.textContent = JSON.stringify(data.summary, null, 2);
                summaryContainer.style.display = 'block';
            } else {
                handleError('Failed to summarize conversation.');
            }
        } catch (error) {
            handleError('Error summarizing conversation.', error);
        }
    }

    // --- UI Helpers ---

    function updateStatus(message) {
        statusDiv.innerText = message;
    }

    function addLogEntry(speaker, text) {
        const entry = document.createElement('div');
        entry.classList.add('log-entry', speaker.toLowerCase());
        entry.innerHTML = `<strong>${speaker}:</strong> ${text}`;
        conversationLog.appendChild(entry);
        conversationLog.scrollTop = conversationLog.scrollHeight; // Auto-scroll
    }

    function handleError(message, error = null) {
        console.error(message, error);
        updateStatus(`Error: ${message}`);
        startBtn.disabled = false;
        startBtn.innerText = 'Try Again';
        startBtn.classList.remove('recording');
        // Reset to a safe state
        isRecording = false;
        conversationStarted = false;
        startBtn.onclick = startConversation;
    }

    // --- Initial Setup ---
    startBtn.onclick = startConversation;
    endBtn.onclick = summarizeConversation;
}); 