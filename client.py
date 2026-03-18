import cv2
import requests
import time
import numpy as np
from picamera2 import Picamera2
from pyzbar import pyzbar

SERVER_URL = "http://localhost:5000/scan"
HEARTBEAT_URL = "http://localhost:5000/heartbeat"

def scan_barcode():
    try:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)})
        picam2.configure(config)
        picam2.set_controls({"AfMode": 2}) 
        picam2.start()

        last_scanned = None
        last_scan_time = 0
        last_heartbeat_time = 0
        heartbeat_interval = 2 

        preview_enabled = False  # toggle state

        while True:
            frame = picam2.capture_array()
            current_time = time.time()

            # Heartbeat
            if current_time - last_heartbeat_time > heartbeat_interval:
                try:
                    requests.post(HEARTBEAT_URL, json={"status": "online"}, timeout=0.5)
                    last_heartbeat_time = current_time
                except:
                    print("Heartbeat failed (Server down?)")

            if frame is None or frame.size == 0:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            barcodes = pyzbar.decode(gray)

            for barcode in barcodes:
                barcode_type = barcode.type
                barcode_data = barcode.data.decode("utf-8")

                if barcode_data != last_scanned or (current_time - last_scan_time > 3):
                    print(f"Detected: {barcode_data} {barcode_type}")
                    if barcode_type == "EAN13" or barcode_type == "CODE128":
                        try:
                            requests.post(SERVER_URL, json={"barcode": barcode_data}, timeout=2)
                            last_scanned = barcode_data
                            last_scan_time = current_time
                        except Exception as e:
                            print(f"Scan upload error: {e}")

            # Show preview if enabled
            if preview_enabled:
                cv2.imshow("Barcode Scanner Preview", frame)

            # Keyboard controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # quit
                break
            elif key == ord('p'):  # toggle preview
                preview_enabled = not preview_enabled
                if not preview_enabled:
                    cv2.destroyWindow("Barcode Scanner Preview")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'picam2' in locals():
            picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_barcode()
