import cv2
import mediapipe as mp
import os
import urllib.request
import serial
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ── CONFIG ───────────────────────────────────────────────────────
SERIAL_PORT  = "COM4"
BAUD_RATE    = 9600
CMD_INTERVAL = 0.15

# ── Connect to TX Arduino ────────────────────────────────────────
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"Connected to TX Nano on {SERIAL_PORT}")
except Exception as e:
    print(f"Serial connection failed: {e}")
    print("Running in DEMO MODE")
    arduino = None

def send_command(cmd):
    if arduino and arduino.is_open:
        arduino.write((cmd + "\n").encode())

# ── Download MediaPipe model ─────────────────────────────────────
MODEL_PATH = "hand_landmarker.task"
if not os.path.exists(MODEL_PATH):
    print("Downloading model (~9MB)...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        MODEL_PATH
    )
    print("Download complete!")

# ── Finger detection ─────────────────────────────────────────────
TIP_IDS = [4, 8, 12, 16, 20]

def fingers_up(landmarks):
    fingers = []
    fingers.append(1 if landmarks[4].x < landmarks[3].x else 0)
    for tip in TIP_IDS[1:]:
        fingers.append(1 if landmarks[tip].y < landmarks[tip - 2].y else 0)
    return fingers

def classify_gesture(f):
    if f == [0, 1, 0, 0, 0]: return ("FORWARD",  "F", (0, 255, 0))
    if f == [0, 1, 1, 0, 0]: return ("BACKWARD", "B", (0, 0, 255))
    if f == [1, 1, 0, 0, 0]: return ("LEFT",     "L", (255, 165, 0))
    if f == [1, 1, 1, 0, 0]: return ("RIGHT",    "R", (255, 200, 0))
    if f == [1, 1, 1, 1, 1]: return ("STOP",     "S", (0, 255, 255))
    if f == [0, 0, 0, 0, 0]: return ("STOP",     "S", (0, 255, 255))
    return                           ("STOP",     "S", (200, 200, 200))

# ── Draw hand landmarks ──────────────────────────────────────────
CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17)
]

def draw_landmarks(frame, landmarks, h, w):
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (255, 255, 255), 2)
    for pt in pts:
        cv2.circle(frame, pt, 5, (0, 255, 0), -1)

# ── MediaPipe setup ──────────────────────────────────────────────
options = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=MODEL_PATH),
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

# ── Webcam ───────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
print("Camera started. Press 'q' to quit.")

last_cmd      = ""
last_cmd_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result   = detector.detect(mp_image)

    label, cmd, color = "No Hand - STOP", "S", (200, 200, 200)

    if result.hand_landmarks:
        for landmarks in result.hand_landmarks:
            draw_landmarks(frame, landmarks, h, w)
            f = fingers_up(landmarks)
            label, cmd, color = classify_gesture(f)

    # Throttled send
    now = time.time()
    if cmd != last_cmd or (now - last_cmd_time) > CMD_INTERVAL:
        send_command(cmd)
        last_cmd      = cmd
        last_cmd_time = now

    # ── HUD ──────────────────────────────────────────────────────
    cv2.rectangle(frame, (0, 0), (700, 70), (0, 0, 0), -1)
    cv2.putText(frame, label, (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

    legend = [
        ("Point  (1 finger)  -> FORWARD",  (0, 255, 0)),
        ("Peace  (2 fingers) -> BACKWARD", (0, 100, 255)),
        ("Gun    (thumb+idx) -> LEFT",     (255, 165, 0)),
        ("3 Fingers          -> RIGHT",    (255, 200, 0)),
        ("Open Hand / Fist   -> STOP",     (0, 255, 255)),
    ]
    for i, (text, c) in enumerate(legend):
        cv2.putText(frame, text, (10, 590 + i * 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, c, 1)

    status       = "Wireless TX: Connected | COM4" if arduino else "DEMO MODE - Check COM Port"
    status_color = (0, 255, 0) if arduino else (0, 0, 255)
    cv2.putText(frame, status, (w - 480, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    cv2.imshow("Gesture Rover - Wireless Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        send_command('S')
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()