import socketio
import time

# Use RPi.GPIO for Raspberry Pi or Mock if testing on PC
try:
    import RPi.GPIO as GPIO
except ImportError:
    from unittest.mock import MagicMock
    GPIO = MagicMock()

# --- Hardware Setup ---
PIN_MOTOR = 17
PIN_ECHO = 24  # Example pins for ultrasonic
PIN_TRIG = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_MOTOR, GPIO.OUT, initial=GPIO.LOW)

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to Flask-SocketIO server.")

@sio.on('activate_mechanism')
def on_activate(data):
    print(f"Server requested bottle intake for: {data.get('item', 'unknown')}")
    
    # 1. Set Pin 17 High
    GPIO.output(PIN_MOTOR, GPIO.HIGH)
    print("Pin 17 HIGH")
    
    # 2. Wait 1 second
    time.sleep(1)
    
    # 3. Set Pin 17 Low
    GPIO.output(PIN_MOTOR, GPIO.LOW)
    print("Pin 17 LOW")

    # 4. Check Ultrasonic (Currently just a dummy check)
    print("Checking ultrasonic sensor for bottle pulse...")
    bottle_detected = True # Placeholder for future logic
    
    if bottle_detected:
        print("Bottle confirmed.")
        sio.emit('bottle_confirmed', {'status': 'success'})
    else:
        sio.emit('bottle_confirmed', {'status': 'failed'})

if __name__ == '__main__':
    sio.connect('http://localhost:5000')
    sio.wait()
