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
        
        decoded_url = unquote(url)
        path = urlparse(decoded_url).path
        clean_path = path.replace('-', ' ').replace('_', ' ').replace('/', ' ').lower()
        
        patterns = {
            'brand': r'(samsung|lg|philips|bosch|siemens|balay|whirlpool|apple|hp|lenovo|acer|asus|msi)',
            'model': r'([a-zA-Z0-9]+-?[a-zA-Z0-9]+)',
            'features': r'(wifi|smart|digital|\d+\s*(gb|tb|inch|pulgadas|\"|cm|kg|w|hz))',
            'category': r'(tv|telefono|portatil|laptop|nevera|lavadora|secadora|monitor)'
        }
        
        extracted_info = {}
        for key, pattern in patterns.items():
            matches = re.finditer(pattern, clean_path, re.IGNORECASE)
            extracted_info[key] = list(set([match.group(0) for match in matches]))
        
        product_description = ' '.join([
            item for sublist in extracted_info.values() 
            for item in sublist
        ])

        print(f"Información extraída: {product_description}")
        return product_description

    def search_product_info(self, product_description):
        """Busca información detallada del producto"""
        print(f"Buscando información para: {product_description}")
        
        try:
            prompt = f"""
            Analiza este producto y proporciona información en este formato:

            ### NOMBRE DEL PRODUCTO
            [Nombre comercial claro y conciso]

            ### PRECIO APROXIMADO
            [Rango de precio en euros]

            ### PERFIL DE USUARIO
            **Ideal para:** [describe el usuario perfecto para este producto]

            ### PUNTOS FUERTES
            • **[Característica Principal]:** [beneficio práctico]
            • **[Segunda Característica]:** [beneficio práctico]
            • **[Tercera Característica]:** [beneficio práctico]

            ### ASPECTOS A CONSIDERAR
            • **[Limitación 1]:** [explicación práctica]
            • **[Limitación 2]:** [explicación práctica]

            Producto a analizar: {product_description}
            """

            messages = [
                {
                    "role": "system",
                    "content": "Eres un experto en tecnología que habla de forma natural y cercana. Da información práctica y útil."
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
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error en búsqueda: {str(e)}")
            return None

    def try_get_product_image(self, url):
        """Intenta obtener la imagen del producto"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                selectors = [
                    'meta[property="og:image"]',
                    'meta[name="twitter:image"]',
                    'meta[property="product:image"]',
                    'img[class*="product-image"]',
                    'img[class*="main-image"]'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        return element.get('content') or element.get('src')
                        
            return None
        except Exception as e:
            print(f"Error obteniendo imagen: {str(e)}")
            return None

    def compare_products(self, products_info):
        """Compara productos con enfoque en uso real y experiencia de usuario"""
        try:
            prompt = f"""
            Como experto asesor que ayuda a amigos a elegir productos, analiza y compara:

            {products_info}

            Estructura tu respuesta exactamente así:

            ### 📌 EN RESUMEN
            **Si buscas la mejor opción calidad-precio:** [Recomendación directa]
            **Si quieres lo mejor sin importar el precio:** [Recomendación directa]
            **Si estás empezando y quieres algo fiable:** [Recomendación directa]

            ### 👥 ¿PARA QUIÉN ES CADA UNO?
            • El primer producto es ideal si:
              - Eres el tipo de persona que [describe situación cotidiana]
              - Tu prioridad es [beneficio principal para el usuario]
              - Valoras especialmente [característica desde punto de vista del usuario]

            • El segundo producto es perfecto cuando:
              - Tu día a día incluye [describe situación cotidiana]
              - Te importa mucho [beneficio principal para el usuario]
              - Necesitas [característica desde punto de vista del usuario]

            ### 🔍 COMPARATIVA PRÁCTICA
            • **En el uso diario:**
              - Primer producto: [Cómo se traduce en experiencia real de uso]
              - Segundo producto: [Cómo se traduce en experiencia real de uso]

            • **Puntos fuertes y débiles:**
              - Primer producto ✅: [3-4 ventajas realmente importantes]
              - Primer producto ⚠️: [1-2 aspectos a considerar]
              - Segundo producto ✅: [3-4 ventajas realmente importantes]
              - Segundo producto ⚠️: [1-2 aspectos a considerar]

            • **Experiencia de uso:**
              - Primer producto: [Cómo se siente usarlo en el día a día]
              - Segundo producto: [Cómo se siente usarlo en el día a día]

            ### 💡 MI CONSEJO SINCERO
            [Escribe un párrafo personal, como si hablaras con un amigo, explicando qué producto recomendarías según diferentes situaciones. Usa ejemplos reales y sé específico sobre qué tipo de usuario se beneficiaría más de cada opción.]

            ### 🎯 RECOMENDACIÓN FINAL
            • **Elige el primer producto si:** [lista de 2-3 situaciones muy específicas]
            • **Elige el segundo producto si:** [lista de 2-3 situaciones muy específicas]
            • **Considera otras opciones si:** [situaciones donde ninguno sería ideal]

            Usa lenguaje coloquial pero profesional, como si estuvieras aconsejando a un amigo. Evita tecnicismos innecesarios y céntrate en la experiencia real de uso.
            """

            messages = [
                {
                    "role": "system",
                    "content": """Eres un experto amigable que ayuda a personas reales a elegir productos.
                    - Habla como si estuvieras charlando con un amigo
                    - Usa ejemplos de la vida real y situaciones cotidianas
                    - Evita especificaciones técnicas a menos que sean realmente relevantes
                    - Explica los beneficios en términos de experiencia de usuario
                    - Da recomendaciones claras basadas en casos de uso reales
                    - Mantén los emojis y el formato especificado
                    - Usa lenguaje cercano pero profesional"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=messages,
                temperature=0.4,
                max_tokens=2500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error en comparación: {str(e)}")
            return None

def analyze_products(urls):
    """Función principal para analizar productos"""
    try:
        analyzer = ProductAnalyzer()
        products_info = []
        
        for url in urls:
            product_description = analyzer.extract_product_info_from_url(url)
            if product_description:
                details = analyzer.search_product_info(product_description)
                image_url = analyzer.try_get_product_image(url)
                if details:
                    products_info.append({
                        "details": details,
                        "image": image_url
                    })
        
        result = None
        if len(products_info) > 1:
            comparison = analyzer.compare_products("\n\n".join([p["details"] for p in products_info]))
            result = {
                "success": True,
                "type": "comparison",
                "analysis": comparison,
                "products": products_info
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
    if len(sys.argv) < 2:
        print("Proporciona al menos una URL")
        sys.exit(1)
    
    analyze_products(sys.argv[1:])