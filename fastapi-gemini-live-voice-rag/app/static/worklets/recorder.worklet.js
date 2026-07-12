// core audio engine

class RecorderProcessor extends AudioWorkletProcessor {

    process(inputs) {
        const input = inputs[0];

        if (input && input[0]) {

            const float32 = input[0];

            const int16 = new Int16Array(float32.length);

            for (let i = 0; i < float32.length; i++) {
                let s = Math.max(-1, Math.min(1, float32[i]));
                int16[i] = s * 32767;
            }

            this.port.postMessage(int16.buffer);
        }

        return true;
    }
}

registerProcessor("recorder", RecorderProcessor);