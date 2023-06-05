import speech_recognition as sr


class SpeechRecognition:
    @staticmethod
    def convert(audio_path: str) -> str:
        recognizer = sr.Recognizer()

        audio_file = sr.AudioFile(audio_path)

        with audio_file as source:
            audio = recognizer.record(source)

        try:
            return recognizer.recognize_google(audio, language='uk-UA')
        except sr.UnknownValueError:
            return 'Помилка: Не вдалося розпізнати голос'
        except sr.RequestError:
            return 'Помилка сервісу розпізнавання'
