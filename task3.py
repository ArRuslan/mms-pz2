import json
import sys

import pyaudio
from vosk import Model, KaldiRecognizer

MODEL_PATH = "/home/ruslan/Downloads/vosk-model-small-uk-v3-small"
SAMPLE_RATE = 16000
CHUNK = 4000


def main():
    try:
        model = Model(MODEL_PATH)
    except Exception as e:
        print("Failed to load model:", e)
        sys.exit(1)

    rec = KaldiRecognizer(model, SAMPLE_RATE)
    pa = pyaudio.PyAudio()

    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print("Listening (press Ctrl+C to stop)...")
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                r = json.loads(rec.Result())
                print(r.get("text", ""))
            else:
                p = json.loads(rec.PartialResult())
                print("[PARTIAL]", p.get("partial", ""), end="\r")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        print("\n", json.loads(rec.FinalResult()).get("text", ""))


if __name__ == "__main__":
    main()
