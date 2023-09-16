import keyboard
from djitellopy import Tello
from utils import cartesian_to_polar
from marker import MarkerDetector, calculate_actual_distance_and_angle
import time
import cv2
import os


class ControleTello:
    def __init__(self, altura):
        self.tello = Tello()
        self.tello.connect()
        self.tello.streamon()
        self.tello.takeoff()
        print("Bateria: ", self.tello.get_battery())
        self.ceramica = 40
        #time.sleep(1)
        self.tello.move_up(altura)
        self.x, self.y, self.yaw = 0, 0, 0
        self.detected_ids = set()

        # Initialize the MarkerDetector
        frame_read = self.tello.get_frame_read()
        self.marker_detector = MarkerDetector(frame_read.frame)
        self.image_dir = "aruco_images"
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
        frame_read = self.tello.get_frame_read()
        processed_frame, marker_data = self.marker_detector.process_frame(
            frame_read.frame
        )

        if marker_data["Target"] is None:
            return processed_frame

        for info in marker_data["Target"]:
            aruco_id = info["id"]

            if aruco_id in self.detected_ids:
                continue

            # Check if this ID has been detected before
            print(
                f"Target ID: {aruco_id}, Distance: {info['distance']}, X Offset: {info['x_offset']}"
            )
            print(
                calculate_actual_distance_and_angle(
                    info["x_offset"], info["distance"], 50
                )
            )

            # Save the image
            image_path = os.path.join(self.image_dir, f"aruco_target_{aruco_id}.jpg")
            cv2.imwrite(image_path, processed_frame)
            print(f"Image saved at {image_path}")

            # Mark this ID as detected
            self.detected_ids.add(aruco_id)

        return processed_frame

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
            ((-11*self.ceramica, 0), 0),
            ((4*self.ceramica, 0), 0),
            ((0, 8*self.ceramica), -180),
            
        ]

    def executar_missao(self, lista_coordenadas):
        for coords in lista_coordenadas:
            angulo_acumulado = 0
            (x_target, y_target), yaw_target = coords
            x_mov, y_mov = (x_target - self.x, y_target - self.y)
            print(f"Initial Angle: {self.yaw}")
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
                self.tello.go_xyz_speed(int(x_target*100), int(y_target * 100), 0, 40)
                if yaw_target > 0:
                    self.tello.rotate_clockwise(yaw_target)
                else:
                    self.tello.rotate_counter_clockwise(yaw_target)
                # angulo_acumulado = angulo - self.yaw
                # print(f"Angulo de movimentação 1: {angulo_acumulado}")
                # self.tello.rotate_clockwise(angulo_acumulado)
                # time.sleep(1)
                # self.tello.move_forward(modulo)
                # time.sleep(1)
                # angulo_acumulado = yaw_target - angulo_acumulado - self.yaw
                # print(f"Angulo de movimentação 2: {angulo_acumulado}")
                # self.tello.rotate_clockwise(angulo_acumulado)
                # time.sleep(1)
                # self.yaw += angulo_acumulado

        if self.tello:
            self.tello.land()


if __name__ == "__main__":
    altura_de_voo = 70
    controle_tello = ControleTello(altura_de_voo)

    missao = controle_tello.missao_1()  # ou missao_1()

    controle_tello.executar_missao(missao)
