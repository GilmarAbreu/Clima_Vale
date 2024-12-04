import time
import random
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import logging

# Configuração de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Clima_Revisado")

# Função para obter dados de clima
def get_weather_data_from_google(city_name):
    url = f"https://www.google.com/search?q=clima+{city_name}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx ou 5xx
        return parse_weather_data(response.text)
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao obter dados de clima para {city_name}: {e}")
        return None

# Função para analisar o HTML e extrair dados meteorológicos
def parse_weather_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    try:
        temperature = soup.find("div", class_="BNeawe iBp4i AP7Wnd").text
        wind_speed = soup.find("span", class_="BNeawe iBp4i AP7Wnd").text
        humidity = soup.find("div", class_="BNeawe tAd8D AP7Wnd").text
        return {
            "temperature": temperature,
            "wind_speed": wind_speed,
            "humidity": humidity
        }
    except AttributeError:
        logger.error("Erro ao analisar os dados de clima.")
        return None

# Função para tentar obter dados com backoff exponencial
def get_weather_data_with_retries(city_name, max_retries=5):
    retries = 0
    while retries < max_retries:
        weather_data = get_weather_data_from_google(city_name)
        if weather_data:  # Se os dados forem válidos, retorna os dados
            return weather_data
        
        retries += 1
        wait_time = random.uniform(2, 5) * retries  # Aumento progressivo do tempo de espera
        logger.info(f"Requisição falhou para {city_name}, tentando novamente em {wait_time:.2f} segundos...")
        time.sleep(wait_time)  # Espera entre tentativas
    
    logger.error(f"Falha ao obter dados de clima após {max_retries} tentativas para {city_name}.")
    return None

# Função para gerar a imagem com os dados meteorológicos
def generate_weather_image(city_name, weather_data):
    # Carregar a imagem base (ou criar uma imagem nova)
    img = Image.new('RGB', (600, 400), color='skyblue')
    draw = ImageDraw.Draw(img)
    
    # Fonte
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()
    
    # Texto para desenhar
    text = f"Clima de {city_name}:\n"
    text += f"Temperatura: {weather_data['temperature']}\n"
    text += f"Vento: {weather_data['wind_speed']}\n"
    text += f"Umidade: {weather_data['humidity']}"
    
    # Desenhar o texto na imagem
    draw.text((50, 50), text, font=font, fill="black")
    
    # Salvar imagem em memória
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)  # Reiniciar a posição do ponteiro
    
    # Retornar a imagem como resposta (poderia retornar como um arquivo, por exemplo)
    return img_byte_arr

# Função principal para lidar com o processamento da requisição
def process_request(city_name):
    # Variável de cache para armazenar dados enquanto o processo está em andamento
    weather_cache = {}

    # Aguardar a obtenção dos dados meteorológicos completos
    logger.info("Aguardando a obtenção de todos os dados meteorológicos...")
    while True:
        # Verifica se todos os dados necessários estão disponíveis
        if city_name not in weather_cache or not weather_cache[city_name]:
            # Tenta obter os dados com tentativas e backoff exponencial
            weather_cache[city_name] = get_weather_data_with_retries(city_name)
        
        # Se os dados estiverem completos, gera a imagem
        if weather_cache[city_name]:
            logger.info(f"Todos os dados de clima para {city_name} foram obtidos com sucesso.")
            img_byte_arr = generate_weather_image(city_name, weather_cache[city_name])
            return img_byte_arr
        
        logger.info(f"Aguardando novos dados para {city_name}...")

# Simulação de uma requisição para a cidade de "Itabira"
if __name__ == "__main__":
    city_name = "Itabira"
    image_data = process_request(city_name)

    # Exemplo de como salvar a imagem gerada
    with open("clima_itabira.png", "wb") as f:
        f.write(image_data.read())
    logger.info("Imagem salva com sucesso!")
