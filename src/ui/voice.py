import pyttsx3
import threading
import queue
import time

class VoiceEngine:
    def __init__(self):
        self.msg_queue = queue.Queue()
        self.stop_flag = False
        self.voice_thread = threading.Thread(target=self._worker, daemon=True)
        self.voice_thread.start()

    def _worker(self):
        """Persistent worker thread for TTS to handle COM initialization correctly."""
        # Initialize engine inside the thread for SAPI5 consistency
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150) # Moderate speed
            
            # Search for Female English voice (like Zira), then Arabic, then default
            voices = engine.getProperty('voices')
            selected_voice = None
            
            # 1. Try to find Female English voice
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    selected_voice = voice.id
                    break
            
            # 2. Try to find Arabic if no female english
            if not selected_voice:
                for voice in voices:
                    if 'arabic' in voice.name.lower():
                        selected_voice = voice.id
                        break
            
            if selected_voice:
                engine.setProperty('voice', selected_voice)
            elif voices:
                engine.setProperty('voice', voices[0].id)
                
            while not self.stop_flag:
                try:
                    text = self.msg_queue.get(timeout=1)
                    if text:
                        engine.say(text)
                        engine.runAndWait()
                    self.msg_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"TTS Worker Error: {e}")
                    # Re-init if it crashed
                    engine = pyttsx3.init()
        except Exception as e:
            print(f"TTS Engine Init Error: {e}")

    def say(self, text):
        """Adds text to the speech queue."""
        if text:
            self.msg_queue.put(text)
