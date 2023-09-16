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


class ControleTello:
    def __init__(self, altura):

        self.x, self.y, self.yaw = 0, 0, 0
        self.saved_picture_ids = set()
        self.Target_ID_saved = False

        # Glitch Strategy
        self.marker_glitch = defaultdict(lambda: {"count": 0, "start_time": None})

        self.mqtt = CronometerMQTT()
        if MQTT:
            self.mqtt.start()
        self.tello = Tello()

        self.tello.connect()
        time.sleep(1) 
        self.tello.streamon()
        time.sleep(1)
        self.tello.takeoff()
        time.sleep(1)
        self.tello.move_up(altura)

        frame_read = self.tello.get_frame_read()
        self.marker_detector = MarkerDetector(frame_read.frame)

        self.image_dir = "aruco_images"
        self.read_ID = 1
        os.makedirs(self.image_dir, exist_ok=True)

        self.define_hotkeys()

    def define_hotkeys(self):
        keyboard.on_press_key("space", self.stop)

    def stop(self, _):
        self.tello.land()
        self.tello.streamoff()
        self.tello.end()
        cv2.destroyAllWindows()
        self.mqtt.stop()
        exit(1)

    def process_frame_for_markers(self):
        while True:
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
                if self.is_glitch(aruco["id"]):
                    continue

                self.mqtt.publish("IDAtual", aruco["id"])
                print(aruco["id"])

                # Teoricamente, aqui já é pra atualizar o Prox_ID

                if aruco["id"] == self.mqtt.prox_id:
                    # TODO: Lógica para o que fazer assim que o target é detectado
                    time.sleep(0.5)
                    while self.mqtt.prox_id == prox_id_aux:
                        # Possível Deadlock caso a Organização não atualize o ProxID
                        self.mqtt.publish("IDAtual", aruco["id"])
                        time.sleep(0.5)
                elif isinstance(self.mqtt.prox_id, list):
                    # TODO: Lógica pro AMR!
                    pass

                # Salvar imagem do Aruco detectado
                # TODO: Salvar uns 3-5 de cada aruco
                self.save_picture(aruco["id"], processed_frame)

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

    def save_picture(self, aruco_id, frame):
        if aruco_id not in self.saved_picture_ids:
            # TODO: add timestamp to image
            image_path = os.path.join(
                self.image_dir, f"aruco_target_{aruco_id}.jpg"
            )
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
            ((0.5, 0), 90),
            ((1, 0), 270),
            ((0, 0), 300),
        ]

    def missao_2(self):
        return [
            ((100, 0), 0),
            ((-100, 0), 0),
            ((100, 0), 0),
            ((-100, 0), 0),
            ((100, 0), 0),
            ((-100, 0), 0),
            ((100, 0), 0),
            ((-100, 0), 0),
        ]

    def executar_missao(self, lista_coordenadas):
        yaw_acumulado = 0
        threading.Thread(target=self.process_frame_for_markers, daemon=True).start()

        for coords in lista_coordenadas:
            angulo_acumulado = 0
            (x_target, y_target), yaw_target = coords
            yaw_target *= -1
            print(f"Initial Angle: {self.yaw}")

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if self.tello:
                time.sleep(1)
                self.tello.go_xyz_speed(x=x_target, y=y_target, z=0, speed=60)
                self.tello.rotate_clockwise(yaw_target)
                yaw_acumulado += yaw_target
                time.sleep(5)
                self.tello.rotate_clockwise(-yaw_acumulado)

        if self.tello:
            self.tello.land()


if __name__ == "__main__":
    altura_de_voo = 20
    controle_tello = ControleTello(altura_de_voo)

    missao = controle_tello.missao_0()  # ou missao_1()

    controle_tello.executar_missao(missao)
