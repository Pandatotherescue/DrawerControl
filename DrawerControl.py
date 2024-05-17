import RPi.GPIO as GPIO
import time
from flask import Flask, request, jsonify  #pip install Flask
from threading import Thread
import requests

app = Flask(__name__)

# GPIO Setup
LOCK_PIN = 17  
SENSOR_PIN = 27 
API_ENDPOINT = ""

GPIO.setmode(GPIO.BCM)
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(LOCK_PIN, GPIO.HIGH) 

def lock():
    GPIO.output(LOCK_PIN, GPIO.HIGH)  # Lock drawer
    print("Drawer is locked")
    return "Drawer is locked"

def unlock():
    GPIO.output(LOCK_PIN, GPIO.LOW)  # Unlock drawer
    print("Drawer is unlocked")
    return "Drawer is unlocked"

def send_data_to_api(data):
    try:
        response = requests.post(API_ENDPOINT, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending data: {e}")

@app.route('/lock', methods=['POST'])
def lock_endpoint():
    message = lock()
    return jsonify({"status": message})

@app.route('/unlock', methods=['POST'])
def unlock_endpoint():
    message = unlock()
    return jsonify({"status": message})

def monitor_sensor():
    while True:
        sensor_state = GPIO.input(SENSOR_PIN)
        if sensor_state == GPIO.LOW:  # triggered alarm for attempted unauthorized access
            print("Unauthorized access detected!")
            data = {"event": "unauthorized_access", "timestamp": time.time()}
            send_data_to_api(data)
        time.sleep(1)

if __name__ == "__main__":
    try:
        # HTTP server
        flask_thread = Thread(target=lambda: app.run(host='10.176.69.*', port=5000))
        flask_thread.start()

        lock()
        print("System ready. Monitoring sensor...")
        monitor_sensor()

    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        GPIO.cleanup()
