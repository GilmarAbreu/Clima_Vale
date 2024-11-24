import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import os
from pytz import timezone

# Configuração do Flask
app = Flask(__name__)

# Chave da API HG Weather
API_KEY = "d13015b5"

# Lista de cidades para consulta, incluindo a coluna "MINA"
CITIES = [
    {"mina": "Cauê, Conceição e Minas do Meio", "nome": "Itabira, MG", "cidade": "Itabira"},
    {"mina": "Capanema", "nome": "Ouro Preto, MG", "cidade": "Ouro Preto"},
    {"mina": "Água Limpa", "nome": "Rio Piracicaba, MG", "cidade": "Rio Piracicaba"},
    {"mina": "Brucutu", "nome": "São Gonçalo do Rio Abaixo, MG", "cidade": "São Gonçalo do Rio Abaixo"},
    {"mina": "Fábrica Nova, Fazendão, Timbopeba e Alegria", "nome": "Mariana, MG", "cidade": "Mariana"},
    {"mina": "Córrego do Meio", "nome": "Sabará, MG", "cidade": "Sabará"},
]

# Caminho para a fonte TTF
FONT_PATH = "./arial.ttf"  # Certifique-se de que essa fonte está no mesmo diretório

def get_weather_data(city_name):
    """Consulta a API HG Weather para obter dados meteorológicos."""
    url = f"https://api.hgbrasil.com/weather?key={API_KEY}&city_name={city_name}"
    response = requests.get(url)
    data = response.json()
    if response.status_code != 200 or "results" not in data:
        return {
            "Temperatura": "N/D", 
            "Condição": "N/D", 
            "Umidade": "N/D", 
            "Vento": "N/D", 
            "Probabilidade de Chuva": "N/D"
        }

    results = data.get("results", {})
    rain_probability = results.get("rain_probability", "N/D") 
    if rain_probability == "N/D" and "forecast" in results:
        rain_probability = results["forecast"][0].get("rain_probability", "N/D")

    return {
        "Temperatura": f"{results.get('temp', 'N/D')}°C",
        "Condição": results.get("description", "N/D"),
        "Umidade": f"{results.get('humidity', 'N/D')}%",
        "Vento": results.get("wind_speedy", "N/D"),
        "Probabilidade de Chuva": f"{rain_probability}%"
    }

@app.route('/dynamic-image')
def generate_image():
    """Gera uma imagem JPG com os dados atualizados."""
    brasil_tz = timezone("America/Sao_Paulo")
    horario_brasil = datetime.now(brasil_tz).strftime('%d/%m/%Y %H:%M:%S')

    width, row_height = 1670, 40  # Mantendo largura total
    header_height = 60
    padding = 63
    total_height = header_height + len(CITIES) * row_height + padding

    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(FONT_PATH, 20)
    font_header = ImageFont.truetype(FONT_PATH, 22)

    title = f"Dados Meteorológicos (Atualizado em {horario_brasil})"
    draw.text((10, 10), title, fill="black", font=font)

    headers = ["Mina", "Cidade", "Temperatura", "Condição", "Umidade", "Vento", "Probabilidade de Chuva"]
    col_widths = [450, 320, 140, 260, 80, 170, 200]  # Ajustando proporções das colunas

    start_x = 10
    y_offset = 50

    # Cabeçalho com centralização
    draw.rectangle([(start_x, y_offset), (width - 10, y_offset + header_height)], outline="black", fill="lightgray")
    for i, header in enumerate(headers):
        text_width = draw.textbbox((0, 0), header, font=font_header)[2]
        text_x = start_x + sum(col_widths[:i]) + (col_widths[i] - text_width) // 2
        draw.text((text_x, y_offset + 15), header, fill="black", font=font_header)
    y_offset += header_height

    # Dados dinâmicos
    for city in CITIES:
        weather = get_weather_data(city["cidade"])
        draw.rectangle([(start_x, y_offset), (width - 10, y_offset + row_height)], outline="black", fill="white")
        draw.text((start_x + 10, y_offset + 10), city["mina"], fill="black", font=font)
        draw.text((start_x + col_widths[0] + 10, y_offset + 10), city["nome"], fill="black", font=font)
        draw.text((start_x + sum(col_widths[:2]) + 10, y_offset + 10), weather["Temperatura"], fill="black", font=font)
        draw.text((start_x + sum(col_widths[:3]) + 10, y_offset + 10), weather["Condição"], fill="black", font=font)
        draw.text((start_x + sum(col_widths[:4]) + 10, y_offset + 10), weather["Umidade"], fill="black", font=font)
        draw.text((start_x + sum(col_widths[:5]) + 10, y_offset + 10), weather["Vento"], fill="black", font=font)
        draw.text((start_x + sum(col_widths[:6]) + 10, y_offset + 10), weather["Probabilidade de Chuva"], fill="black", font=font)
        y_offset += row_height

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/jpeg", as_attachment=False, download_name="dynamic_image.jpg")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
