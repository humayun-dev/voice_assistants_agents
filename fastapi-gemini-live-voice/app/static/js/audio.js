// microphone access
// AudioWorklet setup
// PCM conversion
// local VAD -> explicit turn boundaries (activity_start / activity_end)
// barge-in detection


class AudioHandler {
    constructor(socketClient) {
        this.socketClient = socketClient;
        this.audioContext = null;
        this.processor = null;
        this.source = null;
        this.stream = null;

        this.assistantSpeaking = false;
        this.userTalking = false;
        this.silenceFrames = 0;

        // tune these to your mic/room
        this.START_THRESHOLD = 800;   // RMS level to consider "started talking"
        this.END_SILENCE_MS = 700;    // pause length before considering the turn over
        this.FRAME_MS = 8;            // recorder.worklet.js sends 128-sample chunks @16kHz = 8ms

        this.onBargeIn = null; // set by app.js
    }

    async init() {
        this.audioContext = new AudioContext({ sampleRate: 16000 });

        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        await this.audioContext.audioWorklet.addModule(
            "/static/worklets/recorder.worklet.js"
        );

        this.source = this.audioContext.createMediaStreamSource(this.stream);
        this.processor = new AudioWorkletNode(this.audioContext, "recorder");

        this.processor.port.onmessage = (event) => {
            const audioData = event.data; // raw PCM16 ArrayBuffer
            const volume = this._computeVolume(audioData);
            const isLoud = volume > this.START_THRESHOLD;

            if (isLoud) {
                this.silenceFrames = 0;

                if (!this.userTalking) {
                    this.userTalking = true;

                    if (this.assistantSpeaking && this.onBargeIn) {
                        this.onBargeIn();
                    }

                    this.socketClient.sendControl("activity_start");
                }

                this.socketClient.sendAudio(audioData);

            } else if (this.userTalking) {
                // still forwarding through brief pauses
                this.socketClient.sendAudio(audioData);

                this.silenceFrames += 1;
                const silenceMs = this.silenceFrames * this.FRAME_MS;

                if (silenceMs >= this.END_SILENCE_MS) {
                    this.userTalking = false;
                    this.socketClient.sendControl("activity_end");
                }
            }
            // else: quiet and not currently talking -> send nothing
        };

        this.source.connect(this.processor);
    }

    _computeVolume(arrayBuffer) {
        const samples = new Int16Array(arrayBuffer);
        let sumSquares = 0;
        for (let i = 0; i < samples.length; i++) {
            sumSquares += samples[i] * samples[i];
        }
        return Math.sqrt(sumSquares / samples.length);
    }

    onAssistantSpeakStart() {
        this.assistantSpeaking = true;
    }

    onAssistantSpeakEnd() {
        this.assistantSpeaking = false;
    }

    stop() {
        this.userTalking = false;
        this.assistantSpeaking = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}
