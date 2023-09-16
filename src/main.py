import threading
from collections import defaultdict

import keyboard
from djitellopy import Tello
from marker import MarkerDetector
import time
import cv2
import os
from cronometer_mqtt import CronometerMQTT

MQTT = True

CERAMICA = 40

class ControleTello:
    def __init__(self, altura):

        self.coordinates = [0, 0]
        self.x, self.y, self.yaw = 0, 0, 0
        self.saved_picture_ids = set()
        self.Target_ID_saved = False
        self.should_stop = threading.Event()
        self.should_stop.clear()
        self.is_AMR = False
        self.AMR_dist = None

        # Glitch Strategy
        self.marker_glitch = defaultdict(lambda: {"count": 0, "start_time": None})

        self.mqtt = CronometerMQTT()
        if MQTT:
            self.mqtt.start()
        self.tello = Tello(retry_count=10)
        Tello.RESPONSE_TIMEOUT = 20

        self.tello.connect()
        time.sleep(1)
        print(f"Bateria: {self.tello.get_battery()}")
        self.tello.streamon()
        time.sleep(1)
        self.tello.takeoff()
        time.sleep(1)
        self.tello.move_up(altura)
        time.sleep(1)

        frame_read = self.tello.get_frame_read()
        self.marker_detector = MarkerDetector(frame_read.frame)

        self.image_dir = "aruco_images"
        self.read_ID = 1
        os.makedirs(self.image_dir, exist_ok=True)

        self.define_hotkeys()

    def define_hotkeys(self):
        keyboard.on_press_key("space", self.stop)

    def stop(self, _):
        self.should_stop.set()
        self.tello.end()
        cv2.destroyAllWindows()
        self.mqtt.stop()
        exit(1)

    def process_frame_for_markers(self):
        while not self.should_stop.is_set():
            time.sleep(0.01)
            processed_frame, marker_data = self.marker_detector.process_frame(
                self.tello.get_frame_read().frame
            )

            # Display the processed frame (optional)
            cv2.imshow("Processed Frame", processed_frame)
            cv2.waitKey(1)
            if marker_data["Target"] is None:  # identifica se há target
                continue

            prox_id_aux = self.mqtt.prox_id
            for aruco in marker_data["Target"]:
                if self.should_stop.is_set():
                    break
                if self.is_glitch(aruco["id"]):
                    continue

                self.mqtt.publish("IDAtual", aruco["id"])
                print(aruco["id"])

                # TODO: Logica para voltar a um Waypoint especifico
                # TODO: Logica para armazenar os arucos detectados em um determinado waypoint
                # TODO: Logica para adaptar a trajetoria de waypoints
                #   I.e., se o prox aruco for um aruco já antes detectado

                # Teoricamente, aqui já é pra atualizar o Prox_ID

                timestamp = None
                if aruco["id"] == self.mqtt.prox_id:
                    # TODO: Lógica para o que fazer assim que o target é detectado
                    time.sleep(0.5)
                    while self.mqtt.prox_id == prox_id_aux:
                        # Possível Deadlock caso a Organização não atualize o ProxID
                        self.mqtt.publish("IDAtual", aruco["id"])
                        time.sleep(0.5)
                    timestamp = self.mqtt.tempo_decorrido
                    self.save_picture(aruco["id"], processed_frame, timestamp)
                elif isinstance(self.mqtt.prox_id, list):
                    if aruco['id'] == self.mqtt.prox_id[0]:
                        self.AMR_dist = self.aruco['distance']

                    # TODO: Lógica pro AMR!
                    # Vai para posição próxima ao AMR
                    # Olha pra frente
                    # Espera o AMR passar
                    # Vai para frente devagar até o aruco do AMR sumir do campo de visão
                    # Quando estiver a uma certa distancia, desliga o drone
                    pass

                # Salvar imagem do Aruco detectado
                # TODO: Salvar uns 3-5 de cada aruco
                # self.save_picture(aruco["id"], processed_frame, timestamp)

                # Reset counter and time for Glitch logic
                self.marker_glitch[aruco["id"]]["count"] = 0
                self.marker_glitch[aruco["id"]]["start_time"] = None
        self.stop(None)

    def is_glitch(self, aruco_id):
        if self.marker_glitch[aruco_id]["start_time"] is None:
            self.marker_glitch[aruco_id]["start_time"] = time.time()

        self.marker_glitch[aruco_id]["count"] += 1

        if self.marker_glitch[aruco_id]["count"] < 5:
            return True
        if time.time() - self.marker_glitch[aruco_id]["start_time"] > 2:
            self.marker_glitch[aruco_id]["count"] = 0
            self.marker_glitch[aruco_id]["start_time"] = None
            return True
        return False

    def save_picture(self, aruco_id, frame, timestamp):
        if aruco_id not in self.saved_picture_ids:
            # TODO: add timestamp to image
            image_path = os.path.join(
                self.image_dir, f"aruco_target_{aruco_id} _.jpg"
            )
            # with open("timestamps.txt", "w") as f:
            #     f.write(timestamp)
            cv2.imwrite(image_path, frame)
            print(f"Image saved at {image_path}")

            # Mark this ID as detected
            self.saved_picture_ids.add(aruco_id)
            self.Target_ID_saved = True

    def change_Target(self, new_ID):
        self.Target_ID_saved = False
        self.Target_ID = new_ID

    def missao_0(self):
        return [
            ((1, 0), 0),
            ((0, 0), 0),
        ]

    def missao_1(self):
        return [
            ((CERAMICA*0, 0), 0)
        ]
    def missao_2(self):
        return [
            ((-CERAMICA*5, 0), 0),
            ((-CERAMICA*10, -CERAMICA*2), 0),
            ((-CERAMICA*16, -CERAMICA*4), 150),
            ((-CERAMICA*8, -CERAMICA*9), -45),
            ((-CERAMICA*8, -CERAMICA*9), 45),
            ((-CERAMICA*8, -CERAMICA*18), -45),
            ((0, -CERAMICA*9), 135),
            ((0, -CERAMICA*9), -135),

        ]

    def executar_missao(self, lista_coordenadas):
        threading.Thread(target=self.process_frame_for_markers, daemon=True).start()

        for i, coords in enumerate(lista_coordenadas):
            if self.should_stop.is_set():
                break
            yaw_acumulado = 0
            (x_target, y_target), yaw_target = coords
            print(f"Initial Angle: {self.yaw}")

            if self.tello:
                if i == 5:
                    self.is_AMR = True
                    self.tello.move_down(150)
                    while self.AMR_dist is None:
                        time.sleep(3)
                    # Andar em X ateh que amr dist seja 30
                    # amr dist - 30
                    self.tello.go_xyz_speed(x=int(self.AMR_dist*100)-30, y=0, z=0, speed=40)
                    self.AMR_dist = None
                    # Esperar o aruco 22 do amr aparecer novamente
                    while self.AMR_dist is None:
                        time.sleep(0.01)
                    self.tello.emergency()
                # Calculate relative coordinates
                relative_x = x_target - self.coordinates[0]
                relative_y = y_target - self.coordinates[1]
                if not(relative_x == 0 and relative_y == 0):
                    self.tello.go_xyz_speed(x=relative_x, y=relative_y, z=0, speed=60)
                print(f"Bateria: {self.tello.get_battery()}")
                self.coordinates = [x_target, y_target]  # Update current coordinates
                self.tello.rotate_clockwise(yaw_target)
                yaw_acumulado += yaw_target
                if yaw_target != 0:
                    time.sleep(2)
                    self.tello.rotate_clockwise(-yaw_acumulado)

        if self.tello:
            self.tello.end()


if __name__ == "__main__":
    altura_de_voo = 210
    controle_tello = ControleTello(altura_de_voo)

    missao = controle_tello.missao_2()  # ou missao_1()

    controle_tello.executar_missao(missao)
