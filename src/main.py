from djitellopy import Tello
from utils import cartesian_to_polar
from marker import MarkerDetector, calculate_actual_distance_and_angle
import time
import cv2

class ControleTello:
    def __init__(self, altura):
        self.tello = Tello()
        self.tello.connect()
        self.tello.streamon()
        self.tello.takeoff()
        time.sleep(1)
        self.tello.move_up(altura)
        self.x, self.y, self.yaw = 0, 0, 0

        # Initialize the MarkerDetector
        frame_read = self.tello.get_frame_read()
        self.marker_detector = MarkerDetector(frame_read.frame)

    def process_frame_for_markers(self):
        frame_read = self.tello.get_frame_read()
        processed_frame, marker_data = self.marker_detector.process_frame(frame_read.frame)
        if marker_data['Target'] is not None:
            for info in marker_data['Target']:
                print(f"Target ID: {info['id']}, Distance: {info['distance']}, X Offset: {info['x_offset']}")
                print(calculate_actual_distance_and_angle(info['x_offset'], info['distance'], 50))
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

