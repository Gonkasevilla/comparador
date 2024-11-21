from openai import OpenAI
import re
import json
import sys
import io
import os
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import requests
import argparse

# Configuración para caracteres especiales
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración inicial
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

class ProductAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("No se encontró PERPLEXITY_API_KEY en las variables de entorno")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.perplexity.ai"
        )

    def extract_product_info_from_url(self, url):
        """Extrae información del producto desde la URL"""
        print(f"\nExtrayendo información de URL: {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Intentar obtener el título del producto
            title = None
            title_selectors = [
                'h1[class*="product"]',
                'h1[class*="title"]',
                'h1[itemprop="name"]',
                'meta[property="og:title"]',
                'div[class*="product-title"]'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get('content') or element.text
                    break

            if not title:
                # Extraer información de la URL si no se encuentra en la página
                decoded_url = unquote(url)
                path = urlparse(decoded_url).path
                title = path.replace('-', ' ').replace('_', ' ').replace('/', ' ').strip()

            # Limpiar y formatear el título
            title = re.sub(r'\s+', ' ', title).strip()
            print(f"Título encontrado: {title}")
            return title

        except Exception as e:
            print(f"Error extrayendo información: {str(e)}")
            # Fallback a extracción básica de la URL
            decoded_url = unquote(url)
            path = urlparse(decoded_url).path
            clean_title = path.replace('-', ' ').replace('_', ' ').replace('/', ' ').strip()
            return clean_title

    def search_product_info(self, product_description):
        """Busca información detallada del producto"""
        print(f"Buscando información para: {product_description}")
        
        try:
            prompt = f"""
            Busca y analiza información sobre este producto: {product_description}

            Proporciona un análisis natural y práctico con este formato:

            ### 📱 RESUMEN DEL PRODUCTO
            • **Qué es:** [descripción simple y directa]
            • **Ideal para:** [tipo de usuario ideal]
            • **Precio aproximado:** [rango de precio actual]

            ### ✨ PUNTOS FUERTES
            • [3-4 ventajas principales explicadas en lenguaje cotidiano]

            ### 👥 CASOS DE USO
            • [2-3 situaciones reales donde este producto brilla]

            ### ⚠️ ASPECTOS A CONSIDERAR
            • [2-3 limitaciones o puntos a tener en cuenta]
            """

            messages = [
                {
                    "role": "system",
                    "content": "Eres un experto que habla de forma natural y cercana. Explica las cosas de manera práctica y comprensible."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=messages,
                temperature=0.3,
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error en búsqueda: {str(e)}")
            return None

    def try_get_product_image(self, url):
        """Intenta obtener la imagen del producto"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                selectors = [
                    'meta[property="og:image"]',
                    'meta[name="twitter:image"]',
                    'meta[property="product:image"]',
                    'img[class*="product-image"]',
                    'img[class*="product-main"]',
                    'img[class*="main-image"]'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        image_url = element.get('content') or element.get('src')
                        if image_url:
                            if not image_url.startswith('http'):
                                base_url = urlparse(url)
                                image_url = f"{base_url.scheme}://{base_url.netloc}{image_url}"
                            return image_url
                        
            return None
        except Exception as e:
            print(f"Error obteniendo imagen: {str(e)}")
            return None

    def compare_products(self, products_info, user_context=None):
        """Compara productos con enfoque en uso real y contexto del usuario"""
        try:
            context_part = f"\nTeniendo en cuenta que el usuario busca: {user_context}" if user_context else ""
            
            prompt = f"""
            Como experto asesor de compras, analiza estos productos:{context_part}

            {products_info}

            Proporciona una comparativa natural y práctica con este formato:

            ### 💡 RECOMENDACIÓN RÁPIDA
            **La mejor opción es** [producto] porque [razón simple y directa]
            **También puedes considerar** [otro producto] si [condición específica]

            ### 👤 PARA QUIÉN ES CADA PRODUCTO
            • **El primer producto** es perfecto si:
              - Buscas [beneficio principal]
              - Necesitas [ventaja específica]
              - Valoras [característica importante]

            • **El segundo producto** es ideal si:
              - Prefieres [beneficio principal]
              - Quieres [ventaja específica]
              - Te importa [característica importante]

            ### 💰 RELACIÓN CALIDAD-PRECIO
            • [Análisis del valor por dinero de cada producto]
            • [Justificación de la inversión]

            ### 🎯 EN LA PRÁCTICA
            • **Primer producto:**
              - [Situaciones reales de uso]
              - [Beneficios en el día a día]

            • **Segundo producto:**
              - [Situaciones reales de uso]
              - [Beneficios en el día a día]

            ### 🤝 CONSEJO FINAL
            [Recomendación clara y directa, considerando el contexto si existe]
            """

            messages = [
                {
                    "role": "system",
                    "content": """Eres un experto que asesora en compras de manera cercana y práctica.
                    - Usa lenguaje natural y ejemplos reales
                    - Evita términos demasiado técnicos
                    - Céntrate en beneficios prácticos
                    - Da recomendaciones claras y justificadas
                    - Adapta el consejo al contexto del usuario"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error en comparación: {str(e)}")
            return None

def parse_args():
    parser = argparse.ArgumentParser(description='Analizar y comparar productos')
    parser.add_argument('urls', nargs='+', help='URLs de los productos a comparar')
    parser.add_argument('--context', help='Contexto del usuario')
    return parser.parse_args()

def analyze_products(urls, user_context=None):
    """Función principal para analizar productos"""
    try:
        analyzer = ProductAnalyzer()
        products_info = []
        
        for url in urls:
            product_info = analyzer.extract_product_info_from_url(url)
            if product_info:
                details = analyzer.search_product_info(product_info)
                image_url = analyzer.try_get_product_image(url)
                if details:
                    products_info.append({
                        "details": details,
                        "image": image_url
                    })
        
        if len(products_info) > 1:
            comparison = analyzer.compare_products(
                "\n\n".join([p["details"] for p in products_info]),
                user_context
            )
            result = {
                "success": True,
                "type": "comparison",
                "analysis": comparison,
                "products": products_info,
                "userContext": user_context
            }
        elif len(products_info) == 1:
            result = {
                "success": True,
                "type": "single_product",
                "analysis": products_info[0]["details"],
                "image": products_info[0]["image"]
            }
        else:
            result = {
                "success": False,
                "error": "No se pudo obtener información de los productos"
            }

        print("\nRESULT_JSON_START")
        print(json.dumps(result, ensure_ascii=False))
        print("RESULT_JSON_END")
        return result

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print("\nRESULT_JSON_START")
        print(json.dumps(error_result, ensure_ascii=False))
        print("RESULT_JSON_END")
        return error_result

if __name__ == "__main__":
    args = parse_args()
    analyze_products(args.urls, args.context)