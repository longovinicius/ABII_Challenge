import paho.mqtt.client as mqtt

# Configurações globais do broker
BROKER_ADDRESS = "192.168.137.1"
PORT = 1883

class CronometerMQTT:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.topics = {}
        self.connect()

    def connect(self):
        self.client.connect(BROKER_ADDRESS, PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Conectado com código de resultado {rc}")
        for topic in self.topics:
            client.subscribe(topic)
            print(f"Subscrito ao tópico: {topic}")

    def on_message(self, client, userdata, msg):
        print(f"Nova mensagem recebida no tópico {msg.topic}: {msg.payload.decode()}")
        # Armazenar valores em variáveis de acordo com os tópicos
        if msg.topic in self.topics:
            self.topics[msg.topic] = msg.payload.decode()

    def subscribe_topic(self, topic):
        self.topics[topic] = None
        self.client.subscribe(topic)

    def get_value_for_topic(self, topic):
        return self.topics.get(topic)

    def publish(self, topic, payload):
        self.client.publish(topic, payload, qos=1)
