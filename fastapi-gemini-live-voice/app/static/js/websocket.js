// connects to backend
// sends audio chunks
// receives AI responses 

class SocketClient {
    constructor(url, audioOutput) {
        this.url = url;
        this.ws = null;
        this.audioOutput = audioOutput;
        this.turnBuffer = "";
    }

    connect() {
        this.ws = new WebSocket(this.url);
        this.ws.binaryType = "arraybuffer";

        this.ws.onopen = () => {
            console.log("WebSocket connected");
        };

        this.ws.onmessage = (msg) => {

            const data = msg.data;

            // format: type:content
            const separator = data.indexOf(":");

            if (separator === -1) return;

            const type = data.substring(0, separator);
            const content = data.substring(separator + 1);

            if (type === "text") {
                // accumulate fragments instead of speaking each one
                this.turnBuffer += content;
                console.log("AI (buffering):", content);
            }

            if (type === "status" && content === "turn_complete") {
                if (this.turnBuffer.trim() !== "") {
                    console.log("AI (full turn):", this.turnBuffer);
                    this.audioOutput.speak(this.turnBuffer);
                }
                this.turnBuffer = "";
            }
        };
    }

    sendAudio(data) {
        if (this.ws && this.ws.readyState === 1) {
            this.ws.send(data);
        }
    }

    // plain string -> arrives server-side as a text frame,
    // distinguishable from binary audio chunks
    sendControl(type) {
        if (this.ws && this.ws.readyState === 1) {
            this.ws.send(type);
        }
    }
}