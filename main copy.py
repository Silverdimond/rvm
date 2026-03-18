import cv2
import numpy as np
from picamera2 import Picamera2
from pyzbar import pyzbar
import json


accepted_bottles = json.load(open("bottles.json"))


def scan_barcode():
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)})
    picam2.configure(config)
    picam2.set_controls({"AfMode": 2}) 
    picam2.start()
    print("Scanner started... Press 'q' to quit.")
    try:
        while True:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert to grayscale for faster processing
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Detect barcodes
            barcodes = pyzbar.decode(gray)

            for barcode in barcodes:
                # Extract data and bounding box
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type
                (x, y, w, h) = barcode.rect

                # Draw a rectangle around the barcode
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if barcode_type == "EAN13":
                    if accepted_bottles.get(barcode_data):
                        bottle_name = accepted_bottles[barcode_data]
                        print(f"Accepted Bottle: {bottle_name} (Barcode: {barcode_data})")
                print(f"Found {barcode_type} Barcode: {barcode_data}")
                cv2.putText(frame, barcode_data, (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imshow("PiCam3 Barcode Scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_barcode()