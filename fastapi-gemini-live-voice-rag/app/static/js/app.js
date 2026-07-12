// connects everything together
// handles UI buttons


let socketClient;
let audioHandler;
let audioOutput;
let initialized = false;

document.getElementById("startBtn").onclick = async () => {

    if (initialized) return;

    document.getElementById("status").innerText = "Connecting...";

    audioOutput = new AudioOutput();

    socketClient = new SocketClient(
        "ws://localhost:8000/ws",
        audioOutput
    );

    socketClient.connect();

    audioHandler = new AudioHandler(socketClient);
    await audioHandler.init();

    // mute mic forwarding while assistant speaks, but keep monitoring
    // volume locally so we can detect the user talking over it
    audioOutput.onSpeakStart = () => {
        audioHandler.onAssistantSpeakStart();
        document.getElementById("status").innerText = "🔊 Assistant speaking...";
    };

    // resume forwarding once the assistant finishes naturally
    audioOutput.onSpeakEnd = () => {
        audioHandler.onAssistantSpeakEnd();
        document.getElementById("status").innerText = "Listening 🎤";
    };

    // if the user starts talking while the assistant is speaking,
    // cut the assistant off and immediately resume listening
    audioHandler.onBargeIn = () => {
        audioOutput.stop();  // cancels TTS, also fires onSpeakEnd -> resumes mic
        document.getElementById("status").innerText = "Listening 🎤 (interrupted)";
    };

    initialized = true;

    document.getElementById("status").innerText = "Listening 🎤";
    document.getElementById("startBtn").disabled = true;
    document.getElementById("stopBtn").disabled = false;
};

document.getElementById("stopBtn").onclick = () => {
    if (audioHandler) {
        audioHandler.stop();
    }
    if (audioOutput) {
        audioOutput.stop();
    }
    initialized = false;
    document.getElementById("status").innerText = "Idle";
    document.getElementById("startBtn").disabled = false;
    document.getElementById("stopBtn").disabled = true;
};