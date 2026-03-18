import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import json
import time
import threading
import os


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database setup
accepted_bottles = json.load(open("bottles.json"))

# State variables
current_user = None
session_items = []
last_activity = time.time()
camera_last_seen = 0
SESSION_TIMEOUT = 300  # 5 minutes



def timeout_monitor():
    global current_user, session_items
    while True:
        if current_user and (time.time() - last_activity > SESSION_TIMEOUT):
            print(f"Session for {current_user} timed out.")
            current_user = None
            session_items = []
            socketio.emit('session_end', {'reason': 'timeout'})
        
        camera_status = "online" if (time.time() - camera_last_seen < 10) else "offline"
        socketio.emit('status_ping', {'camera': camera_status})
        time.sleep(1)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/socket.io.js')
def socket_io_js():
    return app.send_static_file('socket.io.js')

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    global camera_last_seen
    camera_last_seen = time.time()
    return jsonify({"status": "received"}), 200

current_user = None
session_points = 0

@socketio.on('connect')
def handle_connect():
    """
    When a new HTML client connects, send it the current session state
    so the UI can be restored after a refresh or reconnect.
    """
    global current_user, session_points, last_activity
    if current_user:
        time_left = max(0, int(SESSION_TIMEOUT - (time.time() - last_activity)))
        emit('restore_state', {
            'user_id': current_user,
            'points': session_points,
            'time_left': time_left
        })

@app.route('/scan', methods=['POST'])
def scan():
    global current_user, session_points, last_activity, camera_last_seen
    barcode = request.json.get("barcode")
    last_activity = time.time()
    camera_last_seen = time.time()

    if not current_user:
        current_user = barcode
        session_points = 0
        socketio.emit('login_success', {'user_id': barcode})
        return jsonify({"status": "logged_in"}), 200

    bottle = accepted_bottles.get(barcode)
    
    if bottle and "сталко" not in bottle.lower():
        session_points += 1
        item = {
            "name": bottle,
            "barcode": barcode,
            "accepted": True,
            "total_points": session_points
        }
        
        socketio.emit('new_item', item)
        socketio.emit('activate_mechanism', {'item': bottle})

        return jsonify({"status": "accepted"}), 200
    else:
        socketio.emit('new_item', {"barcode": barcode, "accepted": False})
        return jsonify({"status": "rejected"}), 200

@app.route('/start_guest', methods=['POST'])
def start_guest():
    global current_user, session_points
    current_user = "GUEST"
    session_points = 0
    socketio.emit('login_success', {'user_id': 'GUEST'})
    return jsonify({"status": "guest_started"}), 200

@app.route('/reset', methods=['POST'])
def reset():
    global current_user, session_points
    socketio.emit('show_summary', {
        'points': session_points,
        'is_guest': (current_user == "GUEST")
    })
    current_user = None
    session_points = 0
    return jsonify({"status": "reset"}), 200

if __name__ == '__main__':
    threading.Thread(target=timeout_monitor, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)
