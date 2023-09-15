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
        time.sleep(1)
        self.tello.move_up(altura)
        self.x, self.y, self.yaw = 0, 0, 0
        self.detected_ids = set()

        # Initialize the MarkerDetector
        frame_read = self.tello.get_frame_read()
        self.marker_detector = MarkerDetector(frame_read.frame)
        self.image_dir = "aruco_images"
        os.makedirs(self.image_dir, exist_ok=True)

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
            (x_novo, y_novo), self.yaw = coords[0]
            self.x += x_novo
            self.y += y_novo
            print(self.x, self.y, self.yaw)
            modulo, angulo = cartesian_to_polar(x_novo, y_novo)
            print(f"{angulo=}")
            print(f"{modulo=}")

            # Process the frame for markers
            processed_frame = self.process_frame_for_markers()

            # Display the processed frame (optional)
            cv2.imshow("Processed Frame", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if self.tello:
                time.sleep(1)
                self.tello.rotate_clockwise(angulo)
                time.sleep(1)
                self.tello.move_forward(modulo)
                time.sleep(1)
                self.tello.rotate_clockwise(lista_coordenadas[i][1])

        if self.tello:
            self.tello.land()


if __name__ == "__main__":
    altura_de_voo = 30
    controle_tello = ControleTello(altura_de_voo)

    missao = controle_tello.missao_0()  # ou missao_1()

    controle_tello.executar_missao(missao)
