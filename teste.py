import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import os

# Configuração do Flask
app = Flask(__name__)

# Chave da API (substitua pela sua APPID)
API_KEY = "f87a22889ea00b7180190cafed52a022"

# Lista de cidades para consulta
CITIES = [
    {"nome": "Itabira, MG", "cidade": "Itabira,br"},
    {"nome": "Ouro Preto, MG", "cidade": "Ouro Preto,br"},
    {"nome": "Rio Piracicaba, MG", "cidade": "Rio Piracicaba,br"},
    {"nome": "São Gonçalo do Rio Abaixo, MG", "cidade": "São Gonçalo do Rio Abaixo,br"},
    {"nome": "Mariana, MG", "cidade": "Mariana,br"},
    {"nome": "Sabará, MG", "cidade": "Sabará,br"},
]

# Caminho para a fonte TTF
FONT_PATH = "./arial.ttf"  # Certifique-se de que essa fonte está no mesmo diretório


def get_weather_data(city_name):
    """Consulta a API OpenWeatherMap para obter a probabilidade de chuva."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric&lang=pt_br"
    response = requests.get(url)
    if response.status_code != 200:
        return "N/D"  # Retorna "Não Disponível" se a API falhar

    data = response.json()
    print(f"Dados recebidos para {city_name}: {data}")  # Debugging

    # Verificar informações do clima
    weather_description = data.get("weather", [{}])[0].get("description", "").lower()
    humidity = data.get("main", {}).get("humidity", 0)
    visibility = data.get("visibility", 10000)

    # Nova lógica para inferir probabilidade de chuva
    if "rain" in weather_description or "chuva" in weather_description:
        return "100%"  # Chuva explícita detectada
    elif humidity > 90 and visibility < 5000:  # Alta umidade e baixa visibilidade
        return "80%"  # Alta chance de chuva
    elif humidity > 80 and visibility < 7000:  # Alta umidade e visibilidade moderada
        return "50%"  # Probabilidade moderada de chuva
    elif "nublado" in weather_description or "cloud" in weather_description:
        return "30%"  # Clima nublado com baixa chance de chuva

    # Verificar precipitação acumulada na última hora
    rain = data.get("rain", {}).get("1h", 0)
    if rain > 0:
        probabilidade = min(max(int(rain * 10), 0), 100)  # Escala simples para probabilidade
        return f"{probabilidade}%"

    # Se não houver chuva detectada
    return "0%"


@app.route('/dynamic-image')
def generate_image():
    """Gera uma imagem JPG com os dados atualizados."""
    # Configuração da imagem
    width, height = 1150, 400
    row_height = 40
    header_height = 60
    total_height = header_height + len(CITIES) * row_height + 20

    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)

    # Carregar fonte TTF
    font = ImageFont.truetype(FONT_PATH, 20)

    # Título
    title = f"Probabilidade de Chuva (Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')})"
    draw.text((10, 10), title, fill="black", font=font)

    # Cabeçalho
    headers = ["MINA", "CORREDOR SUDESTE", "PROBABILIDADE DE CHUVA"]
    col_widths = [500, 350, 250]
    start_x = 10
    y_offset = 50

    # Desenha o cabeçalho com bordas
    draw.rectangle([(start_x, y_offset), (width - 10, y_offset + header_height)], outline="black", fill="lightgray")
    draw.text((start_x + 10, y_offset + 15), f"{headers[0]}", fill="black", font=font)
    draw.text((start_x + col_widths[0], y_offset + 15), f"{headers[1]}", fill="black", font=font)
    draw.text((start_x + col_widths[0] + col_widths[1], y_offset + 15), f"{headers[2]}", fill="black", font=font)
    y_offset += header_height

    # Dados dinâmicos
    minas = [
        "Cauê, Conceição e Minas do Meio",
        "Capanema",
        "Água Limpa",
        "Brucutu",
        "Fábrica Nova, Fazendão, Timbopeba e Alegria",
        "Córrego do Meio",
    ]

    for mina, city in zip(minas, CITIES):
        probabilidade = get_weather_data(city["cidade"])

        # Desenha a linha de dados
        draw.rectangle([(start_x, y_offset), (width - 10, y_offset + row_height)], outline="black", fill="white")
        draw.text((start_x + 10, y_offset + 10), f"{mina}", fill="black", font=font)
        draw.text((start_x + col_widths[0], y_offset + 10), f"{city['nome']}", fill="black", font=font)
        draw.text((start_x + col_widths[0] + col_widths[1], y_offset + 10), f"{probabilidade}", fill="black", font=font)
        y_offset += row_height

    # Salvar imagem em um buffer
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/jpeg", as_attachment=False, download_name="dynamic_image.jpg")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
