import requests
import threading
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_alert(image_path, caption="🚨 Motion Detected"):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[NOTIFY] Telegram credentials missing")
        return

    def _send():
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        try:
            with open(image_path, 'rb') as img_file:
                payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
                files = {'photo': img_file}
                response = requests.post(url, data=payload, files=files, timeout=10)
                if response.status_code == 200:
                    print("[NOTIFY] Telegram Alert Sent!")
                else:
                    print(f"[NOTIFY] Failed: {response.text}")
        except Exception as e:
            print(f"[NOTIFY] Error sending alert: {e}")

    threading.Thread(target=_send).start()
