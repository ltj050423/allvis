# stream_server.py
from flask import Flask, Response, request, render_template
try:
    from picamera2 import Picamera2 #only imports on raspberry pi.
except:
    print("picamera2 is not importable. it could be a 'not raspberry pi' or 'did not installed package' problem.")
import io
import time
import threading
import cv2
import serial

app = Flask(__name__) #create flask object.

picam2 = Picamera2() #create Picamera object.
config = picam2.create_video_configuration(
    main={"size": (640, 480),
          "format": "RGB888"

            })

try:
    arduino = serial.Serial(
        port = "/dev/ttyACM0",
        baudrate=9600,
        timeout=0.2
    )

except:
    print("arduino is not responding. camera only.")

try:    
    picam2.configure(config)#configure Picamera object.
    picam2.start() #start Picamera object.
except:
    pass

lock = threading.Lock()

def generate_frames(): #capture frame with camera and converts to jpg.
    while True:
        with lock:
            frame = picam2.capture_array() #picam에서 캡쳐.

        # YUV2 -> JPEG 인코딩
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n'
        )

@app.route('/stream')
def stream():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pan/<direction>')
def pan_control(direction):
    commands = {"left" : "-90\n", "right" : "+90\n"}
    if direction in commands:
        arduino.write(commands[direction].encode())
        return f"OK: {direction}"
    else:
        return "unknown command", 400

if __name__ == '__main__':  
    app.run(host='0.0.0.0', port=8083, threaded=True)
