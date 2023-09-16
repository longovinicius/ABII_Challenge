import paho.mqtt.client as mqtt


class CronometerMQTT:
    def __init__(self, host="127.0.0.1", port=1883):
        self.host = host
        self.port = port

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.prox_id = 1
        self.tempo_decorrido = None

    def on_connect(self, client, userdata, flags, rc):
        """Callback function to handle the connection"""
        __mqtt_rc = {
            0: "Connection successful",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorised",
        }
        print(__mqtt_rc.get(rc))
        if rc == 0:
            self.client.subscribe("ProximoID", qos=1)
            self.client.subscribe("TempoDecorrido", qos=1)

    def on_message(self, client, userdata, msg):
        # Armazenar valores em variáveis de acordo com os tópicos
        payload = msg.payload.decode()
        if msg.topic == "ProximoID":
            try:
                self.prox_id = int(payload)
            except ValueError:
                self.prox_id = eval(payload)
            finally:
                print(f"Next ID: {self.prox_id}")

        elif msg.topic == "TempoDecorrido":
            self.tempo_decorrido = payload

    def publish(self, topic, payload):
        self.client.publish(topic, payload, qos=1)

    def start(self):
        """Start the MQTT client"""
        self.client.connect(self.host, self.port, 60)
        self.client.loop_start()

    def stop(self):
        """Stop the MQTT client"""
        self.client.loop_stop()
