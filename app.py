import threading
import sys
from web_server import start_server
from log_manager import logger

cam = None

def start_camera():
    global cam
    from camera_core import CameraCore
    import web_server
    cam = CameraCore()
    web_server.camera_instance = cam
    cam.run()

def main():
    logger.log("System Initializing...")
    cam_thread = threading.Thread(target=start_camera, daemon=True)
    cam_thread.start()
    logger.log("Web Server Starting...")
    try:
        start_server(None)
    except KeyboardInterrupt:
        logger.log("Stopping System...")
        sys.exit(0)

if __name__ == "__main__":
    main()
