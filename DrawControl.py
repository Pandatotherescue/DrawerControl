import RPi.GPIO as GPIO
import time
from flask import Flask, request, jsonify  # pip install Flask
from threading import Thread
import requests
import socket
import json
import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C

app = Flask(__name__)

# GPIO Setup
LOCK_PIN = 17
SENSOR_PIN = 27
API_ENDPOINT = "http://10.176.69.180:4000/logs"

GPIO.setmode(GPIO.BCM)
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(LOCK_PIN, GPIO.HIGH)

ip_addr = "10.176.69.22"

# NFC Setup
i2c = busio.I2C(board.SCL, board.SDA)
reset_pin = DigitalInOut(board.D4)
req_pin = DigitalInOut(board.D5)
pn532 = PN532_I2C(i2c, debug=False, reset=reset_pin, req=req_pin)

# Check PN532 connection
ic, ver, rev, support = pn532.firmware_version
print(f"Found PN532 with firmware version: {ver}.{rev}")

pn532.SAM_configuration()

def check_status():
    state = GPIO.input(LOCK_PIN)
    return int(state)

def time_check():
    timestamp = int(time.time() * 1000)
    print(timestamp)
    return timestamp

def format_json(timestamp, ip_addr, state):
    data = {
        "timestamp": str(timestamp),
        "ip": ip_addr,
        "status": str(state)
    }
    return data

def lock():
    GPIO.output(LOCK_PIN, GPIO.LOW)  # Lock drawer
    return "Drawer is locked"

def unlock():
    GPIO.output(LOCK_PIN, GPIO.HIGH)  # Unlock drawer
    return "Drawer is unlocked"

def send_data_to_api(sens_trigger=False):
    timestamp = time_check()
    state = 2 if sens_trigger else check_status()
    serialized_json = format_json(timestamp, ip_addr, state)
    json_data = json.dumps(serialized_json)
    print(json_data)

    try:
        response = requests.post(url=API_ENDPOINT, json=serialized_json)
        print(response.text)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending data: {e}")

@app.route('/status', methods=['GET'])
def status_endpoint():
    return jsonify({"status": check_status()})

@app.route('/lock', methods=['POST'])
def lock_endpoint():
    message = lock()
    send_data_to_api()
    return jsonify({"status": message})

@app.route('/unlock', methods=['POST'])
def unlock_endpoint():
    message = unlock()
    send_data_to_api()
    return jsonify({"status": message})

def monitor_sensor():
    while True:
        sensor_state = GPIO.input(SENSOR_PIN)
        if sensor_state == GPIO.LOW: 
            print("Unauthorized access detected!")
            send_data_to_api(True)
        time.sleep(3)

def monitor_nfc():
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid is not None:
            print("NFC tag detected!")
            send_data_to_api()
            unlock()
        time.sleep(1)

if __name__ == "__main__":
    try:
        # HTTP server
        flask_thread = Thread(target=lambda: app.run(host='10.176.69.22', port=5000))
        flask_thread.start()

        lock()
        print("System ready. Monitoring sensor and NFC...")

        sensor_thread = Thread(target=monitor_sensor)
        sensor_thread.start()

        nfc_thread = Thread(target=monitor_nfc)
        nfc_thread.start()

        sensor_thread.join()
        nfc_thread.join()
      
    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        GPIO.cleanup()
