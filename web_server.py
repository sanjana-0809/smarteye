from flask import Flask, render_template, Response, jsonify
import os
import time
from config import CAPTURE_DIR
from log_manager import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
camera_instance = None

def gen_frames():
    while True:
        if camera_instance:
            frame = camera_instance.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033)

@app.route('/')
def index():
    captures = []
    if os.path.exists(CAPTURE_DIR):
        captures = sorted(os.listdir(CAPTURE_DIR), reverse=True)[:10]
    return render_template('index.html', captures=captures)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/current_frame')
def current_frame():
    if camera_instance:
        frame = camera_instance.get_frame()
        if frame:
            return Response(frame, mimetype='image/jpeg')
    return '', 204

@app.route('/api/logs')
def get_logs():
    return jsonify(logger.get_logs())

@app.route('/api/status')
def get_status():
    if camera_instance is None:
        return jsonify({'status': 'LOADING', 'fps': 0, 'model_ready': False})
    return jsonify({
        'status': 'ALERTED' if camera_instance.in_alert_state else 'ARMED',
        'fps': round(camera_instance.fps, 1),
        'model_ready': camera_instance.model_ready
    })

def start_server(cam_obj):
    global camera_instance
    camera_instance = cam_obj
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)