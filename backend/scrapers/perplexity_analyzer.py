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
    try:
        context_part = f"\nEl usuario está interesado en: {user_context}." if user_context else ""

        prompt = f"""
        Soy un experto en compras y te ayudaré a decidir entre estos productos.{context_part}

        Aquí tienes la comparativa que pediste:

        ### 💡 RECOMENDACIÓN RÁPIDA
        • **Mejor opción:** [Producto A] porque [razón directa y clara].
        • **Otra opción interesante:** [Producto B], especialmente si [razón específica].

        ### 👤 ¿PARA QUIÉN ES CADA PRODUCTO?
        **Producto A:**
        • Ideal para quienes [beneficio principal].
        • Perfecto para [tipo de usuario o contexto].
        • Excelente opción si necesitas [característica clave].

        **Producto B:**
        • Recomendado para [beneficio principal].
        • Mejor opción para quienes buscan [ventaja específica].
        • Adecuado para [tipo de situación].

        ### 📊 DIFERENCIAS CLAVE
        • **Rendimiento:** [compara ventajas de ambos productos].
        • **Diseño:** [detalla diferencias visibles o funcionales].
        • **Extras:** [comenta características únicas o destacables].

        ### 💰 RELACIÓN CALIDAD-PRECIO
        • **Producto A:** [valor y beneficios por el precio].
        • **Producto B:** [valor y beneficios por el precio].
        • **Resumen:** [cuál ofrece mejor relación calidad-precio].

        ### 🤝 CONSEJO FINAL
        Basándome en lo que buscas, te recomiendo [producto recomendado] porque [razón final]. Espero que esta comparativa te ayude a decidir.
        """

        messages = [
    {
        "role": "system",
        "content": """Eres un asesor de compras amable, cercano y confiable.
        - Habla como si estuvieras ayudando a un amigo a elegir el mejor producto.
        - Usa un lenguaje simple, claro y positivo, evitando jerga técnica.
        - Organiza las ideas con listas y emojis en los títulos para que sean fáciles de entender.
        - Resalta puntos clave con negritas (**texto**) y da ejemplos claros y prácticos para respaldar tus recomendaciones.
        - Usa un tono emocionado y útil, enfocándote en lo que hace especial cada producto y cómo mejora la vida del usuario.
        - Sé breve pero completo. Evita abrumar al usuario con detalles innecesarios."""
    },
    {
        "role": "user",
        "content": prompt
    }
]


        return messages

    except Exception as e:
        print(f"Error en la generación del prompt: {str(e)}")
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