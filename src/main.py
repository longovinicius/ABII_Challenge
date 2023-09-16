import keyboard
from djitellopy import Tello
from utils import cartesian_to_polar
from marker import MarkerDetector, calculate_actual_distance_and_angle
import time
import cv2
import os
from cronometer_mqtt import CronometerMQTT

CERAMICA = 40

class ControleTello:
    def __init__(self, altura):
        self.tello = Tello()
        self.tello.connect()
        time.sleep(1)
        self.tello.streamon()
        time.sleep(1)
        self.tello.takeoff()
        time.sleep(1)
        #self.tello.move_up(altura)
        self.coordinates = [0, 0]
        # self.x, self.y, self.yaw = 0, 0, 0
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

        self.define_hotkeys()

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
                pass

            if aruco_id not in self.saved_picture_ids:
                image_path = os.path.join(self.image_dir, f"aruco_target_{aruco_id}.jpg")
                cv2.imwrite(image_path, processed_frame)
                print(f"Image saved at {image_path}")

                # Mark this ID as detected
                self.detected_ids.add(aruco_id)
                self.Target_ID_saved = True

        return processed_frame

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
            ((-CERAMICA*12, 0), 0),
            ((-CERAMICA*16, -CERAMICA*8), 180),
            ((-CERAMICA*12, 0), 0),
            ((0, 0), 0)
        ]

    def executar_missao(self, lista_coordenadas):
        yaw_acumulado = 0
        for coords in lista_coordenadas:
            angulo_acumulado = 0
            (x_target, y_target), yaw_target = coords
            yaw_target *= -1

            # Process the frame for markers
            processed_frame = self.process_frame_for_markers()

            # Display the processed frame (optional)
            # cv2.imshow("Processed Frame", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if self.tello:
                time.sleep(1)
                relative_x = x_target - self.coordinates[0]
                relative_y = y_target - self.coordinates[1] 
                self.tello.go_xyz_speed(x=relative_x, y=relative_y, z=0, speed=60)
                self.coordinates = [x_target, y_target]
                if yaw_target > 0:
                    self.tello.rotate_clockwise(yaw_target)
                    yaw_acumulado += yaw_target
                    time.sleep(5)
                    self.tello.rotate_clockwise(-yaw_acumulado)

        if self.tello:
            self.tello.land()


if __name__ == "__main__":
    altura_de_voo = 70
    controle_tello = ControleTello(altura_de_voo)

    missao = controle_tello.missao_2()  # ou missao_1()

    controle_tello.executar_missao(missao)
