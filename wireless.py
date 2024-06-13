import wifi, socketpool

def connect():
    try:
        print("connecting to wifi ...")
        wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
        time.sleep(10)
    except:
        print("unable to connect to wifi ...")
    
    print("Connected to WiFi")
