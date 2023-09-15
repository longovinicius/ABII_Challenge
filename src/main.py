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
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

    def process_frame_for_markers(self):
        frame_read = self.tello.get_frame_read()
        processed_frame, marker_data = self.marker_detector.process_frame(frame_read.frame)
        
        if marker_data['Target'] is not None:
            for info in marker_data['Target']:
                aruco_id = info['id']
                
                # Check if this ID has been detected before
                if aruco_id not in self.detected_ids:
                    
                    print(f"Target ID: {aruco_id}, Distance: {info['distance']}, X Offset: {info['x_offset']}")
                    print(calculate_actual_distance_and_angle(info['x_offset'], info['distance'], 50))
                    
                    # Save the image
                    image_path = os.path.join(self.image_dir, f"aruco_target_{aruco_id}.jpg")
                    cv2.imwrite(image_path, processed_frame)
                    print(f"Image saved at {image_path}")
                    
                    # Mark this ID as detected
                    self.detected_ids.add(aruco_id)

        return processed_frame

    def missao_1(self):
        lista_coordenadas = []
        lista_coordenadas.append(((3, 0), 0))
        lista_coordenadas.append(((0, -3), 90))
        lista_coordenadas.append(((-2, 3), 180))
        return lista_coordenadas
    def missao_2(self):
        lista_coordenadas = []
        lista_coordenadas.append(((2, 0), 0))
        lista_coordenadas.append(((0, 2), 0))
        lista_coordenadas.append(((3, 0), 90))
        lista_coordenadas.append(((1, 0), 0))
        lista_coordenadas.append(((0, 1), 90))
        lista_coordenadas.append(((0, 1), 0))
        lista_coordenadas.append(((-1, 0), 90))
        lista_coordenadas.append(((-2, 0), 90))
        return lista_coordenadas
    
    def executar_missao(self, lista_coordenadas):
        for i in range(len(lista_coordenadas)):
            x_novo, y_novo = lista_coordenadas[i][0]
            self.x += x_novo
            self.y += y_novo
            self.yaw = lista_coordenadas[i][1]
            print(self.x, self.y, self.yaw)
            modulo, angulo = cartesian_to_polar(lista_coordenadas[i][0])
            print(angulo)
            print(modulo)

            # Process the frame for markers
            processed_frame = self.process_frame_for_markers()

            # Display the processed frame (optional)
            cv2.imshow("Processed Frame", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
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
    altura_de_voo = 185
    controle_tello = ControleTello(altura_de_voo)
    
    missao = controle_tello.missao_1()  # ou missao_1()
    
    controle_tello.executar_missao(missao)

