import os
import re
from datetime import datetime
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image
from PIL.ExifTags import TAGS
import time

# Configurações de credenciais e endpoint da Azure
subscription_key = "your subscription here"
endpoint = "your endpoint here"

# Cria o cliente do Computer Vision
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Função para extrair a data da imagem usando OCR da Azure
def extract_date(image_path):
    with open(image_path, "rb") as image_stream:
        ocr_result = computervision_client.read_in_stream(image_stream, language="en", raw=True)
        operation_location_remote = ocr_result.headers["Operation-Location"]
        operation_id = operation_location_remote.split("/")[-1]

        # Espera até que o OCR esteja concluído
        while True:
            get_handw_text_results = computervision_client.get_read_result(operation_id)
            if get_handw_text_results.status not in ['running']:
                break
            time.sleep(1)

        if get_handw_text_results.status == 'succeeded':
            for text_result in get_handw_text_results.analyze_result.read_results:
                for line in text_result.lines:
                    # Usar regex para encontrar datas nos formatos especificados
                    match = re.search(r'\b\d{2}[/\.]\d{2}[/\.]\d{4}\b', line.text)
                    if match:
                        # Padroniza o formato da data para DD/MM/AAAA
                        return match.group(0).replace('.', '/')
    return None

# Função para obter a data de criação dos metadados EXIF
def get_exif_creation_date(image_path):
    image = Image.open(image_path)
    exif_data = image._getexif()
    
    if exif_data:
        for tag, value in exif_data.items():
            decoded_tag = TAGS.get(tag, tag)
            if decoded_tag == "DateTimeOriginal":
                return value
    return None

# Função para atualizar os metadados EXIF com a data extraída
def update_exif(image_path, date):
    image = Image.open(image_path)
    exif = image.info.get('exif')
    
    if exif:
        # Converter a data extraída para o formato EXIF (YYYY:MM:DD HH:MM:SS)
        day, month, year = date.split('/')
        current_time = datetime.now().strftime('%H:%M:%S')
        exif_date = f"{year}:{month}:{day} {current_time}"

        # Atualizar o campo DateTimeOriginal
        exif_dict = {TAGS.get(k, k): v for k, v in image._getexif().items() if k in TAGS}
        exif_dict['DateTimeOriginal'] = exif_date
        
        # Atualizar os metadados EXIF
        exif_bytes = image.info['exif']
        image.save(image_path, "jpeg", exif=exif_bytes)
        
        return image_path
    return None

# Função para processar todas as imagens em uma pasta
def process_images_in_folder(folder_path):
    if not os.path.exists("updated_images"):
        os.makedirs("updated_images")

    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(folder_path, filename)
            print(f"Processando imagem: {image_path}")
            date = extract_date(image_path)
            if date:
                print(f"Data encontrada na imagem: {date}")
                updated_image_path = update_exif(image_path, date)
                if updated_image_path:
                    print(f"Metadados EXIF atualizados na imagem: {updated_image_path}")
                else:
                    print("Não foi possível atualizar os metadados EXIF.")
            else:
                print(f"Data não encontrada na imagem!")
                creation_date = get_exif_creation_date(image_path)
                if creation_date:
                    print(f"Data de criação nos metadados EXIF: {creation_date}")
                else:
                    print("Data não encontrada na imagem e não há data de criação nos metadados EXIF.")

# Caminho para a pasta de entrada
folder_path = r"your photo path here"

# Processa todas as imagens na pasta
process_images_in_folder(folder_path)
