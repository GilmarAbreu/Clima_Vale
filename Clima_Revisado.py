from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import os
from pytz import timezone
import requests
from bs4 import BeautifulSoup
import logging

# Configuração do Flask
app = Flask(__name__)

# Configuração de Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lista de cidades para consulta
CITIES = [
    {"mina": "Cauê, Conceição e Minas do Meio", "nome": "Itabira, MG", "cidade": "Itabira"},
    {"mina": "Capanema", "nome": "Ouro Preto, MG", "cidade": "Ouro Preto"},
    {"mina": "Água Limpa", "nome": "Rio Piracicaba, MG", "cidade": "Rio Piracicaba"},
    {"mina": "Brucutu", "nome": "São Gonçalo do Rio Abaixo, MG", "cidade": "São Gonçalo do Rio Abaixo"},
    {"mina": "Fábrica Nova, Fazendão, Timbopeba e Alegria", "nome": "Mariana, MG", "cidade": "Mariana"},
    {"mina": "Córrego do Meio", "nome": "Sabará, MG", "cidade": "Sabará"},
    {"mina": "Gongo Soco", "nome": "Barão de Cocais, MG", "cidade": "Barão de Cocais"}
]

# Caminho para a fonte TTF
FONT_PATH = "./arial.ttf"

def get_weather_data_from_google(city_name):
    """Extrai os dados meteorológicos da página do Google em português."""
    query = f"clima {city_name.replace(' ', '+')}"
    url = f"https://www.google.com/search?q={query}&hl=pt-BR&gl=br"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extrair dados da página do Google
        rain_probability = soup.find("span", {"id": "wob_pp"}).text.strip()
        temperature = soup.find("span", {"id": "wob_tm"}).text.strip()
        humidity = soup.find("span", {"id": "wob_hm"}).text.strip()
        wind = soup.find("span", {"id": "wob_ws"}).text.strip()
        condition = soup.find("span", {"id": "wob_dc"}).text.strip()

        # Conversões
        temperature_celsius = f"{temperature}°C"  # Google já retorna em Celsius
        wind_speed_kmh = f"{int(float(wind.split()[0]) * 1.60934)} km/h"  # Convertendo mph para km/h

        return {
            "Temperatura": temperature_celsius,
            "Condição": condition,
            "Umidade": humidity,
            "Vento": wind_speed_kmh,
            "Probabilidade de Chuva": rain_probability
        }
    except (requests.RequestException, AttributeError, ValueError) as e:
        logger.error(f"Erro ao obter dados de clima: {e}")
        return {
            "Temperatura": "N/D",
            "Condição": "N/D",
            "Umidade": "N/D",
            "Vento": "N/D",
            "Probabilidade de Chuva": "N/D"
        }

@app.route('/dynamic-image')
def generate_image():
    """Gera uma imagem JPG com os dados atualizados."""
    logger.info("Rota /dynamic-image acessada.")
    try:
        brasil_tz = timezone("America/Sao_Paulo")
        horario_brasil = datetime.now(brasil_tz).strftime('%d/%m/%Y %H:%M:%S')

        width, row_height = 1700, 40
        header_height = 60
        padding = 63
        total_height = header_height + len(CITIES) * row_height + padding

        image = Image.new("RGB", (width, total_height), "white")
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype(FONT_PATH, 20)
        font_header = ImageFont.truetype(FONT_PATH, 22)

        title = f"Dados Meteorológicos (Atualizado em {horario_brasil})"
        draw.text((10, 10), title, fill="black", font=font)

        headers = ["MINA", "CIDADE", "TEMPERATURA", "CONDIÇÃO", "UMIDADE", "VENTO", "PROBAB. CHUVA"]
        col_widths = [450, 320, 140, 350, 70, 155, 185]

        start_x = 10
        y_offset = 50

        # Cabeçalho
        draw.rectangle([(start_x, y_offset), (width - 10, y_offset + header_height)], outline="black", fill="#4C9ED9")
        for i, header in enumerate(headers):
            bbox = draw.textbbox((0, 0), header, font=font_header)
            text_width = bbox[2] - bbox[0]
            text_x = start_x + sum(col_widths[:i]) + (col_widths[i] - text_width) // 2
            draw.text((text_x, y_offset + 15), header, fill="white", font=font_header)
        y_offset += header_height

        # Dados
        for i, city in enumerate(CITIES):
            weather = get_weather_data_from_google(city["cidade"])
            row_color = "#f4f4f4" if i % 2 == 0 else "#e0e0e0"
            draw.rectangle([(start_x, y_offset), (width - 10, y_offset + row_height)], outline="black", fill=row_color)

            # Escrever dados
            draw.text((start_x + 10, y_offset + 10), city["mina"], fill="black", font=font)
            draw.text((start_x + col_widths[0] + 10, y_offset + 10), city["nome"], fill="black", font=font)

            row_data = [
                weather["Temperatura"],
                weather["Condição"],
                weather["Umidade"],
                weather["Vento"],
                weather["Probabilidade de Chuva"]
            ]
            col_indices = [2, 3, 4, 5, 6]
            for i, data in enumerate(row_data):
                col_index = col_indices[i]
                bbox = draw.textbbox((0, 0), data, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = start_x + sum(col_widths[:col_index]) + (col_widths[col_index] - text_width) // 2
                draw.text((text_x, y_offset + 10), data, fill="black", font=font)

            y_offset += row_height

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        return send_file(buffer, mimetype="image/jpeg", as_attachment=False, download_name="dynamic_image.jpg")
    except Exception as e:
        logger.error(f"Erro ao gerar imagem: {e}")
        return "Erro ao gerar imagem", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
