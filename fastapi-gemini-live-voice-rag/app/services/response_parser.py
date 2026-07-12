class GeminiResponseParser:

    def parse(self, message: dict):
        """
        Convert a raw Live API (BidiGenerateContent) server message into a
        clean format for the frontend.

        Live API messages look like one of:
          {"setupComplete": {}}
          {"serverContent": {"modelTurn": {"parts": [{"text": "..."}]}, "turnComplete": true}}
          {"serverContent": {"modelTurn": {"parts": [{"inlineData": {...}}]}}}
          {"serverContent": {"interrupted": true}}
          {"toolCall": {...}}
        NOT the REST generateContent shape ("candidates"), which never
        appears here.
        """

        try:
            # ---------------------------
            # SESSION HANDSHAKE
            # ---------------------------
            if "setupComplete" in message:
                return {"type": "status", "content": "setup_complete"}

            # ---------------------------
            # MODEL TURN (text / audio parts)
            # ---------------------------
            server_content = message.get("serverContent")

            if server_content:

                if server_content.get("interrupted"):
                    return {"type": "status", "content": "interrupted"}

                model_turn = server_content.get("modelTurn")

                if model_turn:
                    for part in model_turn.get("parts", []):
                        if "inlineData" in part:
                            # raw audio bytes from the native-audio model —
                            # ignored here since we use the transcript instead
                            pass

                # Native-audio models return the spoken text separately
                # as a transcript, not as a text part in modelTurn.
                output_transcription = server_content.get("outputTranscription")
                if output_transcription and output_transcription.get("text"):
                    return {"type": "text", "content": output_transcription["text"]}

                if server_content.get("turnComplete"):
                    return {"type": "status", "content": "turn_complete"}

            # ---------------------------
            # UNKNOWN / UNHANDLED EVENT
            # ---------------------------
            return {
                "type": "raw",
                "content": message
            }

        except Exception as e:
            return {
                "type": "error",
                "content": str(e)
            }