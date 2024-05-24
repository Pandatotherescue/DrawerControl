import RPi.GPIO as GPIO
import time
from flask import Flask, request, jsonify  #pip install Flask
from threading import Thread
import socket
import requests
#------------------------------------------------------------------------------
# TO DO LIST:
#   1.  Færdiggør data formattering (jsonify)
#           {"Timestamp ": local_time, "IP ": ipAddr, "Status ": checkStatus}  - skal muligvis rettes til  !!!
#
#   2.  Indsæt de sidste end-points
#           * Data til API
#           * API til Admin-Client
#
#   3.  Test ALLE end-points
#           * -> API -> Redis
#           * -> API -> Admin-Client
#
#------------------------------------------------------------------------------


app = Flask(__name__)

# GPIO Setup
LOCK_PIN = 17  
SENSOR_PIN = 27 
API_ENDPOINT = "/test"

#JSON Data points
hostname = socket.gethostname()
ipAddr = socket.gethostbyname(hostname)

currentTime = time.time()
local_time = time.ctime(currentTime)

GPIO.setmode(GPIO.BCM)
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(LOCK_PIN, GPIO.HIGH) 

def checkStatus():
    state = GPIO.input(17)
    return bool(state)  

def lock():
    GPIO.output(LOCK_PIN, GPIO.LOW)  # Lock drawer
    print("Drawer is locked  " + str(checkStatus()))
    return "Drawer is locked"

def unlock():
    GPIO.output(LOCK_PIN, GPIO.HIGH)  # Unlock drawer
    print("Drawer is unlocked  " + str(checkStatus()))
    return "Drawer is unlocked"


def send_data_to_api(data):
    try:
        response = requests.post(API_ENDPOINT, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending data: {e}")

@app.route('/status', methods=['GET'])
def status_endpoint():
    print(checkStatus())
    message = checkStatus()
    return jsonify({"status": checkStatus()})

@app.route('/lock', methods=['POST'])
def lock_endpoint():
    print("Request LOCK")
    message = lock()
    return jsonify({"status": message})

@app.route('/unlock', methods=['POST'])
def unlock_endpoint():
    print("Request UNLOCK")
    message = unlock()
    testJsonify = jsonify({"status": message})
    print(testJsonify)
    return testJsonify

def monitor_sensor():
    while True:
        sensor_state = GPIO.input(SENSOR_PIN)

        if sensor_state == GPIO.LOW:  # Hvis sensor aktiveres
            print("Unauthorized access attempt detected!")
            data = {"event": "unauthorized_access", "timestamp": time.time()}
            send_data_to_api(data)
        
        time.sleep(0.1)


if __name__ == "__main__":
    try:
        # HTTP server
        flask_thread = Thread(target=lambda: app.run(host='10.176.69.22', port=5000))
        flask_thread.start()
        
        lock()
        print("System ready. Monitoring sensor...")
        
        sensor_thread = Thread(target=monitor_sensor)
        
        sensor_thread.start()
        sensor_thread.join()
        

    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        GPIO.cleanup()
