from collections import deque
from datetime import datetime
import threading

class LogManager:
    def __init__(self):
        self.logs = deque(maxlen=50)
        self.lock = threading.Lock()

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        with self.lock:
            self.logs.appendleft(entry)

    def get_logs(self):
        with self.lock:
            return list(self.logs)

logger = LogManager()
