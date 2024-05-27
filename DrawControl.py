import RPi.GPIO as GPIO
import time
from flask import Flask, request, jsonify  #pip install Flask
from threading import Thread
import requests
import socket
import json

app = Flask(__name__)

# GPIO Setup
LOCK_PIN = 17  
SENSOR_PIN = 27 
API_ENDPOINT = "http://<insert ip>:4000/logs"

GPIO.setmode(GPIO.BCM)
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.output(LOCK_PIN, GPIO.HIGH) 

ip_addr = "<insert ip>"

def checkStatus():
    state = GPIO.input(17)
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

def send_data_to_api(sens_trigger = False):

    timestamp = time_check()

    state = 2 if sens_trigger else checkStatus()
    
    ip = ip_addr
    serialized_json = format_json(timestamp, ip, state)
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
    return jsonify({"status": checkStatus()})

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

        if sensor_state == GPIO.LOW:  # Hvis sensor aktiveret
            print("Unauthorized access detected!")
            
            send_data_to_api(True)
            
        time.sleep(3)

if __name__ == "__main__":
    try:
        # HTTP server
        flask_thread = Thread(target=lambda: app.run(host='<insert ip>', port=5000))
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
