import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def convert_images_to_pdf(input_dir, output_pdf):
    # Lista todos os arquivos no diretório de entrada
    files = os.listdir(input_dir)

    # Filtra apenas os arquivos de imagem (extensões suportadas)
    image_files = [
        file
        for file in files
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))
    ]

    # Abre o arquivo PDF para escrita
    c = canvas.Canvas(output_pdf, pagesize=letter)

    for image_file in image_files:
        # Abre cada imagem usando o Pillow
        image_path = os.path.join(input_dir, image_file)
        image = Image.open(image_path)

        # Calcula o tamanho da imagem em relação à página PDF
        width, height = letter
        img_width, img_height = image.size
        aspect_ratio = img_width / img_height
        if img_width > width or img_height > height:
            if aspect_ratio >= 1:
                img_width = width
                img_height = img_width / aspect_ratio
            else:
                img_height = height
                img_width = img_height * aspect_ratio

        # Adiciona a imagem ao PDF
        c.drawImage(image_path, 0, 0, img_width, img_height)
        c.showPage()

    # Fecha o arquivo PDF
    c.save()


if __name__ == "__main__":
    input_directory = "aruco_images/aruco_target_4.jpg"  # Substitua pelo caminho do seu diretório de imagens
    output_pdf = "saida.pdf"  # Caminho para o arquivo PDF de saída

    convert_images_to_pdf(input_directory, output_pdf)
