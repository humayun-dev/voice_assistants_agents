class AudioOutput {
    constructor() {
        this.speaking = false;
    }

    speak(text) {

        if (!text || text.trim() === "") return;

        const utterance = new SpeechSynthesisUtterance(text);

        // voice tuning for assistant feel
        utterance.rate = 1.05;
        utterance.pitch = 1;
        utterance.volume = 1;

        utterance.onstart = () => {
            this.speaking = true;
            console.log("🔊 Speaking:", text);
        };

        utterance.onend = () => {
            this.speaking = false;
            console.log("Done speaking");
        };

        speechSynthesis.speak(utterance);
    }

    stop() {
        speechSynthesis.cancel();
        this.speaking = false;
    }
}