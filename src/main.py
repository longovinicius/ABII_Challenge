import keyboard
from djitellopy import Tello
from utils import cartesian_to_polar
from marker import MarkerDetector, calculate_actual_distance_and_angle
import time
import cv2
import os
from cronometer_mqtt import CronometerMQTT

class ControleTello:
    def __init__(self, altura):
        self.tello = Tello()
        self.tello.connect()
        self.tello.streamon()
        self.tello.takeoff()
        time.sleep(1)
        #self.tello.move_up(altura)
        self.x, self.y, self.yaw_atual = 0, 0, 0
        self.saved_picture_ids = []
        self.detected_ids = []
        self.Target_ID_saved = False

        # Initialize the MarkerDetector
        frame_read = self.tello.get_frame_read()
        self.marker_detector = MarkerDetector(frame_read.frame)
        self.image_dir = "aruco_images"
        self.read_ID = 1
        self.Target_ID = 1
        os.makedirs(self.image_dir, exist_ok=True)

    def define_hotkeys(self):
        keyboard.on_press_key("space", self.stop)

    def stop(self, _):
        self.tello.land()
        self.tello.streamoff()
        self.tello.end()
        cv2.destroyAllWindows()
        exit(1)

    def process_frame_for_markers(self):

        self.detected_ids = []

        frame_read = self.tello.get_frame_read()
        processed_frame, marker_data = self.marker_detector.process_frame(
            frame_read.frame
        )

        if marker_data["Target"] is None:  # identifica se há target
            return processed_frame 

        for info in marker_data["Target"]:
            aruco_id = info["id"]

            self.detected_ids.append(aruco_id)  # Armazena target em detected_ids
            if aruco_id == self.Target_ID:
                subscriber.publish("Proximo_ID", aruco_id)
                time.sleep(0.5)
                subscriber.get_value_for_topic()

            if aruco_id not in self.saved_picture_ids:
                image_path = os.path.join(self.image_dir, f"aruco_target_{aruco_id}.jpg")
                cv2.imwrite(image_path, processed_frame)
                print(f"Image saved at {image_path}")

                # Mark this ID as detected
                self.detected_ids.add(aruco_id)
                self.Target_ID_saved = True

            # if aruco_id == self.Target_ID: 
            #     image_path = os.path.join(self.image_dir, f"aruco_target_{aruco_id}.jpg")
            #     cv2.imwrite(image_path, processed_frame)
            #     print(f"Image saved at {image_path}")

            #     # Mark this ID as detected
            #     self.detected_ids.add(aruco_id)
            #     self.Target_ID_saved = True

        return processed_frame
    
    def change_Target(self, new_ID):
        self.Target_ID_saved = False
        self.Target_ID = new_ID

    def missao_0(self):
        return [
            ((1, 0), 90),
            ((0, 0), 180),
        ]

    def missao_1(self):
        return [
            ((3, 0), 0),
            ((0, -3), 90),
            ((-2, 3), 180),
        ]

    def missao_2(self):
        return [
            ((2, 0), 0),
            ((0, 2), 0),
            ((3, 0), 90),
            ((1, 0), 0),
            ((0, 1), 90),
            ((0, 1), 0),
            ((-1, 0), 90),
            ((-2, 0), 90),
        ]

    def executar_missao(self, lista_coordenadas):
        for coords in lista_coordenadas:
            angulo_acumulado = 0
            (x_target, y_target), yaw_target = coords
            x_mov, y_mov = (x_target - self.x, y_target - self.y)
            print(f"Initial Angle: {self.yaw_atual}")
            modulo, angulo = cartesian_to_polar(x_mov, y_mov)
            print(f"Angulo Calculado Cartesiano: {angulo}")
            self.x += x_target
            self.y += y_target
            
            print(f"{angulo=}")
            print(f"{modulo=}")

            # Process the frame for markers
            processed_frame = self.process_frame_for_markers()

            # Display the processed frame (optional)
            # cv2.imshow("Processed Frame", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if self.tello:
                time.sleep(1)
                angulo_acumulado = angulo - self.yaw
                print(f"Angulo de movimentação 1: {angulo_acumulado}")
                self.tello.rotate_clockwise(angulo_acumulado)
                time.sleep(1)
                self.tello.move_forward(modulo)
                time.sleep(1)
                angulo_acumulado = yaw_target - angulo_acumulado - self.yaw
                print(f"Angulo de movimentação 2: {angulo_acumulado}")
                self.tello.rotate_clockwise(angulo_acumulado)
                time.sleep(1)
                self.yaw += angulo_acumulado

        if self.tello:
            self.tello.land()


if __name__ == "__main__":
    import time
    start = time.time()
    subscriber = CronometerMQTT()
    subscriber.subscribe_topic("ProximoID")
    subscriber.subscribe_topic("TempoDecorrido")
    while True:
        now = time.time()
        TARGET_ID = subscriber.get_value_for_topic("ProximoID")
        time_stamp = subscriber.get_value_for_topic("TempoDecorrido")
        print(f"ID: {TARGET_ID}")
        print(f"TIME: {time_stamp}")
        time.sleep(1)
        if now - start > 10:
            subscriber.publish("StopCronometro","true")
        altura_de_voo = 30
    controle_tello = ControleTello(altura_de_voo)

    missao = controle_tello.missao_0()  # ou missao_1()

    controle_tello.executar_missao(missao)
