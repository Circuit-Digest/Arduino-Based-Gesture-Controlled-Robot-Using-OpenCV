# Arduino-Based Gesture-Controlled Robot Using OpenCV

Gesture-controlled robotics replaces traditional buttons and joysticks with natural hand movements, improving user interaction and reducing mechanical dependency on physical controllers. Sensors capture motion, convert it into digital data, and translate that data into robot movement in real time.

This project demonstrates a gesture-controlled robot using a **laptop webcam**, **OpenCV**, and **MediaPipe** for real-time hand detection. Hand gestures captured by the camera control the robot's direction, while an **nRF24L01** radio module transmits commands wirelessly from a transmitter Arduino Nano to a receiver Arduino Nano mounted on the rover. The **L298N motor driver** on the receiver side converts those commands into motor actions.

The design focuses on clarity, reliability, and low-cost components that makers can easily source and assemble. This setup forms a strong foundation for advanced human-machine interaction projects.



## Table of Contents

- [System Overview and Working Principle](#system-overview-and-working-principle)
- [Hardware Components Used](#hardware-components-used)
- [nRF24L01 Wireless Module Overview](#nrf24l01-wireless-module-overview)
- [Pin Connections](#pin-connections)
- [OpenCV and Python Installation](#opencv-and-python-installation)
- [How OpenCV and MediaPipe Work Together](#how-opencv-and-mediapipe-work-together)
- [Gesture Detection](#gesture-detection)
- [Wireless Communication Using nRF24L01](#wireless-communication-using-nrf24l01)
- [Source Code Explanation](#source-code-explanation)
- [Testing and Output](#testing-and-output)
- [Applications](#applications)
- [Future Enhancements](#future-enhancements)
- [FAQs](#faqs)
- [License](#license)


## System Overview and Working Principle

This gesture-controlled robot operates using a **three-part wireless control architecture**:

1. A **Python program** running on the laptop captures hand gestures via the webcam, recognizes them using OpenCV and MediaPipe, and sends serial commands to the transmitter Arduino Nano.
2. The **transmitter** forwards those commands wirelessly to the receiver Nano on the rover.
3. The **receiver Nano** drives the motors through the L298N motor driver.

### Data Flow

```
Webcam → Python (OpenCV + MediaPipe) → USB Serial → TX Arduino Nano → nRF24L01 (wireless) → RX Arduino Nano → L298N Motor Driver → DC Motors
```

The Python application processes each camera frame in real time. MediaPipe detects **21 landmarks** on the hand, and the program uses the relative positions of fingertips and knuckles to determine which fingers are raised. Each finger pattern maps to a specific movement command such as Forward, Backward, Left, Right, or Stop.

After determining the required action, Python sends a **single-character command** over USB serial to the transmitter Nano. The transmitter packages it and sends it wirelessly using the nRF24L01 module. The receiver Nano stays in constant listening mode and executes the motor routine as soon as a valid command arrives.

## Hardware Components Used

| Component | Quantity | Purpose |
|---|---|---|
| Arduino Nano | 2 | Transmitter & Receiver microcontrollers |
| nRF24L01 Wireless Module | 2 | Wireless command transmission |
| L298N Motor Driver | 1 | DC motor speed & direction control |
| 4-Wheel DC Gear Motor Chassis | 1 | Robot body with motors |
| Laptop with Webcam | 1 | Gesture capture & processing |
| External 12V Battery Pack | 1 | Motor power supply |
| Jumper Wires and Breadboard | — | Circuit connections |

## nRF24L01 Wireless Module Overview

The nRF24L01 is a low-power wireless transceiver designed for short-range communication. It operates in the **2.4 GHz ISM band** and supports fast, reliable data transfer between microcontrollers. The module uses **SPI communication**, which allows the Arduino Nano to send and receive data with precise timing and control.

In this project, the nRF24L01 works in a **point-to-point configuration**. One module stays in transmit mode on the controller side, while the other stays in receive mode on the robot side.

## Pin Connections

### nRF24L01 → Arduino Nano (Same for Both TX and RX)

| nRF24L01 Pin | Arduino Nano Pin |
|---|---|
| GND | GND |
| VCC | 3.3V |
| CSN | D8 |
| CE | D9 |
| MOSI | D11 |
| MISO | D12 |
| SCK | D13 |

### Transmitter Connections

The transmitter unit connects to the laptop via USB. It receives single-character serial commands from the Python gesture script and forwards them wirelessly to the rover using the nRF24L01 module.

**Data Flow:**
```
Laptop (Python) → USB Serial → Arduino Nano TX → nRF24L01 → Rover
```

### Receiver → L298N Motor Driver Connections

The receiver unit sits on the rover and connects to the L298N motor driver.

| L298N Pin | Arduino Nano Pin | Function |
|---|---|---|
| IN1 | D2 | Motor A Direction 1 |
| IN2 | D3 | Motor A Direction 2 |
| IN3 | D4 | Motor B Direction 1 |
| IN4 | D6 | Motor B Direction 2 |
| ENA | D5 (PWM) | Motor A Speed Control |
| ENB | D10 (PWM) | Motor B Speed Control |
| GND | GND | Common Ground |
| +12V | External Battery | Motor Power |
| +5V | Nano VIN | Logic Power |

---

## OpenCV and Python Installation

### Step 1: Install Python

Download **Python 3.10 or 3.11** from [python.org](https://python.org). During installation, check the option **"Add Python to PATH"**.

### Step 2: Create Project Folder and Virtual Environment

Open Command Prompt and run:

```bash
mkdir hand_gesture_project
cd hand_gesture_project
python -m venv venv
venv\Scripts\activate
```

> **Note:** The `(venv)` prefix in the terminal confirms the environment is active.

### Step 3: Install Required Libraries

```bash
pip install opencv-python mediapipe pyserial
```

| Library | Purpose |
|---|---|
| `opencv-python` | Camera capture and image frame processing |
| `mediapipe` | Google hand landmark detection (21 points per hand) |
| `pyserial` | USB serial communication with Arduino TX Nano |

### Step 4: Download the MediaPipe Hand Landmarker Model

On the first run, the Python script **automatically downloads** the `hand_landmarker.task` model file (~9MB) from Google. An internet connection is required only for this one-time download.

## How OpenCV and MediaPipe Work Together

OpenCV captures frames from the laptop webcam as NumPy arrays in BGR format. Each frame is flipped horizontally for a natural mirror effect, then converted to RGB before being passed to MediaPipe. MediaPipe processes the frame and returns the X, Y coordinates of **21 hand landmarks**.

| Landmark Index | Body Part |
|---|---|
| 0 | Wrist |
| 4 | Thumb Tip |
| 8 | Index Finger Tip |
| 12 | Middle Finger Tip |
| 16 | Ring Finger Tip |
| 20 | Pinky Tip |

## Gesture Detection

The Python script detects hand gestures by analyzing the positions of 21 hand landmarks. A finger is considered **raised** when its tip landmark has a lower Y coordinate than its middle knuckle landmark on screen (since Y increases downward in image coordinates). The thumb uses the **X axis** for comparison since it moves horizontally.

### Gesture Mapping

| Gesture | Fingers Up | Command | Rover Action |
|---|---|---|---|
| Point (index only) | `[0,1,0,0,0]` | `F` | Move Forward |
| Peace / V sign | `[0,1,1,0,0]` | `B` | Move Backward |
| Gun (thumb + index) | `[1,1,0,0,0]` | `L` | Turn Left |
| Three fingers | `[1,1,1,0,0]` | `R` | Turn Right |
| Open hand | `[1,1,1,1,1]` | `S` | Stop |
| Fist | `[0,0,0,0,0]` | `S` | Stop |

> Commands are throttled to send at most once every **150 milliseconds** to prevent flooding the serial port. If no hand is detected, a **Stop** command is sent automatically to keep the rover safe.

## Wireless Communication Using nRF24L01

Both modules are configured with the same pipe address, channel, data rate, and power level:

- **Pipe Address:** `"00001"`
- **Power Level:** `RF24_PA_LOW` — improves stability at short range and reduces power consumption
- **Channel:** 108 — avoids interference from common WiFi bands
- **Payload:** Single character (`F`, `B`, `L`, `R`, or `S`) in a 2-byte packet

## Source Code Explanation

### 📁 Project Structure

```
├── Source Code/
│   ├── Arduino/
│   │   ├── Transmitter/
│   │   │   └── Transmitter.ino      # TX Nano code
│   │   └── Receiver/
│   │       └── Receiver.ino          # RX Nano code (rover)
│   └── Python/
│       └── hand_gesture_project/
│           ├── gesture.py            # Python gesture detection script
│           └── hand_landmarker.task  # MediaPipe model (auto-downloaded)
├── Images/
└── README.md
```

### Python Gesture Detection Script (`gesture.py`)

This script runs on the laptop. It captures webcam frames, detects hand landmarks using MediaPipe, classifies the gesture, and sends the command character over serial to the TX Nano.

**Serial Connection:**

```python
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
except Exception as e:
    arduino = None
```

The two-second sleep is important because Arduinos reboot the moment a serial connection is made. If the connection fails, it sets `arduino` to `None` and keeps running in demo mode.

**Automatic Model Download:**

```python
if not os.path.exists(MODEL_PATH):
    urllib.request.urlretrieve(
        'https://storage.googleapis.com/mediapipe-models/...',
        MODEL_PATH)
```

**Finger Detection Logic:**

```python
fingers.append(1 if landmarks[4].x < landmarks[3].x else 0)  # Thumb (horizontal)
for tip in TIP_IDS[1:]:
    fingers.append(1 if landmarks[tip].y < landmarks[tip-2].y else 0)  # Other fingers (vertical)
```

**Gesture Classification:**

```python
if f == [0,1,0,0,0]: return ('FORWARD',  'F', (0,255,0))
if f == [0,1,1,0,0]: return ('BACKWARD', 'B', (0,0,255))
if f == [1,1,0,0,0]: return ('LEFT',     'L', (255,165,0))
if f == [1,1,1,0,0]: return ('RIGHT',    'R', (255,200,0))
if f == [1,1,1,1,1]: return ('STOP',     'S', (0,255,255))
```

---

### Arduino Transmitter Code (`Transmitter.ino`)

This program runs on the TX Nano connected to the laptop via USB. It reads single-character serial commands from Python and transmits them wirelessly.

```cpp
#include <SPI.h>
#include <RF24.h>

RF24 radio(9, 8);  // CE=D9, CSN=D8
const byte address[6] = "00001";
```

- `radio.begin()` initializes the nRF24 module with error checking
- `openWritingPipe(address)` sets the transmission address
- `setPALevel(RF24_PA_LOW)` sets low power for short-range use
- `stopListening()` sets the module to transmitter mode

Valid commands (`F`, `B`, `L`, `R`, `S`) are packaged into a 2-byte payload and sent wirelessly via `radio.write()`.

### Arduino Receiver Code (`Receiver.ino`)

This sketch runs on the Nano mounted on the rover. It listens for wireless commands and drives the motors at **50% speed** (`motorSpeed = 128`) through the L298N motor driver.

```cpp
#define IN1 2    // Motor A Direction 1
#define IN2 3    // Motor A Direction 2
#define IN3 4    // Motor B Direction 1
#define IN4 6    // Motor B Direction 2
#define ENA 5    // Motor A Speed (PWM)
#define ENB 10   // Motor B Speed (PWM)

int motorSpeed = 128;  // 50% of 255
```

Motor functions:

| Function | Motor A (IN1/IN2) | Motor B (IN3/IN4) | Result |
|---|---|---|---|
| `moveForward()` | HIGH/LOW | HIGH/LOW | Both motors forward |
| `moveBackward()` | LOW/HIGH | LOW/HIGH | Both motors backward |
| `turnLeft()` | LOW/HIGH | HIGH/LOW | Left motor back, right forward |
| `turnRight()` | HIGH/LOW | LOW/HIGH | Left motor forward, right back |
| `stopMotors()` | LOW/LOW | LOW/LOW | All motors stop (speed = 0) |


## Testing and Output

Follow this sequence for a reliable first test:

1. **Upload TX code** to the Nano connected to the laptop. Open Serial Monitor (9600 baud) and type `F` — confirm it prints `Sent: F`.
2. **Connect the RX Nano** to the laptop separately. Open its Serial Monitor and check it prints `Received: F` when TX sends.
3. **Close ALL Serial Monitors** before running Python.
4. **Mount the RX Nano** on the rover and connect to L298N. Power rover with a 12V battery.
5. **Run** `python gesture.py` on the laptop. Show hand gestures to the camera and observe the rover movement.

> ⚠️ **Important:** Python and Arduino IDE Serial Monitor cannot share the same COM port simultaneously. Always close the Serial Monitor before running the Python script.

## Applications

- Remote-controlled robotic vehicles and surveillance rovers
- Assistive robots for basic mobility tasks
- Educational platforms for learning computer vision and embedded systems
- Human-machine interface experimentation
- Contactless control systems for hazardous environments
- Prototype control models for industrial robotics and automation

## Future Enhancements

- Add **two-hand gesture support** for simultaneous speed and direction control
- Implement **variable motor speed** based on finger count or hand distance from the camera
- Add **obstacle detection** using ultrasonic or IR sensors on the rover
- Replace character commands with **structured data packets** for higher efficiency
- Use **external antenna nRF24L01** modules to improve wireless range
- Add a **real-time video stream** from a camera mounted on the rover
- Train a **custom gesture classifier** using scikit-learn for more gesture variety

## FAQs

<details>
<summary><strong>Why does the nRF24L01 require 3.3V power?</strong></summary>
<br>
The nRF24L01 uses internal RF circuitry that operates strictly at 3.3V. Supplying 5V damages the internal transceiver permanently. Even brief exposure to higher voltage causes unstable transmission or complete module failure. A regulated 3.3V supply with proper grounding ensures stable wireless performance.
</details>

<details>
<summary><strong>Why is the Serial Monitor closed before running Python?</strong></summary>
<br>
Python and Arduino IDE Serial Monitor cannot share the same COM port simultaneously. Whichever opens first locks the port, blocking the other. Always close the Serial Monitor before running the Python script, or it will fail to connect with a <code>Permission Denied</code> error.
</details>

<details>
<summary><strong>Why is motor speed limited to 50%?</strong></summary>
<br>
The L298N and DC gear motors can draw more than 5A at full speed under load, which risks overheating the motor driver and draining the battery rapidly. Setting <code>motorSpeed</code> to 128 out of 255 limits PWM duty cycle to 50%, keeping current draw within safe limits while still providing sufficient torque.
</details>

<details>
<summary><strong>What is the maximum operating range of the system?</strong></summary>
<br>
Using <code>RF24_PA_LOW</code>, the reliable range is typically 10 to 30 meters indoors, depending on obstacles and interference. Switching to <code>RF24_PA_HIGH</code> with a decoupling capacitor across the nRF24 VCC and GND pins can extend the range further.
</details>

<details>
<summary><strong>Can this work without a virtual environment?</strong></summary>
<br>
Yes, but a virtual environment is strongly recommended. It prevents library version conflicts between projects. If using PowerShell, activate with <code>venv\Scripts\Activate.ps1</code> after enabling script execution, or switch to Command Prompt and use <code>venv\Scripts\activate</code> instead.
</details>

<details>
<summary><strong>What if the rover moves in the wrong direction?</strong></summary>
<br>
Swap the <code>IN1</code> and <code>IN2</code> definitions in the RX Arduino code for the affected motor side. Alternatively, physically swap the two motor wires going into the L298N output terminals for that channel. No hardware damage occurs from reversed motor polarity.
</details>

---

## License

This project is open-source and available under the [MIT License](LICENSE).

---

<p align="center">
  <b>If you found this project helpful, give it a ⭐ on GitHub!</b>
</p>
