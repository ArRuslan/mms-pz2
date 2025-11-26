import speech_recognition as sr
from speech_recognition.recognizers import google as sr_google

def main(languages: list[str] | None = None) -> None:
    if languages is None:
        languages = ["en-US"]

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Calibrating microphone... please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening continuously. Press Ctrl+C to stop.")

        while True:
            try:
                audio = recognizer.listen(source)

                for lang in languages:
                    try:
                        text = sr_google.recognize_legacy(recognizer, audio, language=lang)
                        print(f"[{lang}] -> {text}")
                        break
                    except sr.UnknownValueError:
                        continue

                else:
                    print("Could not understand audio in any language.")

            except KeyboardInterrupt:
                print("\nStopped.")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    language_list = ["en-US", "uk-UA"]
    main(language_list)
