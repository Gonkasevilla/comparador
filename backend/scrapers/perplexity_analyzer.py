from openai import OpenAI
import re
import json
import sys
import io
import os
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
from pathlib import Path
import argparse

# Configuración para caracteres especiales
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración de rutas y variables de entorno
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

class ProductAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('PERPLEXITY_API_KEY'),
            base_url="https://api.perplexity.ai"
        )

    def extract_product_info_from_url(self, url):
        """Extrae información relevante de la URL del producto"""
        try:
            # Decodificar URL
            decoded_url = unquote(url)
            parsed_url = urlparse(decoded_url)
            
            # Extraer nombre del producto de la URL
            path_parts = parsed_url.path.split('/')
            product_name = next((part for part in reversed(path_parts) if part), '')
            
            # Limpiar el nombre
            product_name = product_name.replace('-', ' ').replace('_', ' ')
            product_name = re.sub(r'\.html$', '', product_name)
            
            # Extraer palabras clave
            keywords = re.findall(r'\b\w+\b', product_name.lower())
            
            print(f"Extrayendo información de URL: {url}")
            print(f"Información extraída: {' '.join(keywords)}")
            
            return ' '.join(keywords)

        except Exception as e:
            print(f"Error extrayendo información: {str(e)}")
            return None

    def compare_products(self, products_info, user_context=None):
        try:
            context_part = f"\nTeniendo en cuenta que el usuario busca: {user_context}" if user_context else ""
            
            products = products_info.split("\n\n")
            product1 = products[0] if len(products) > 0 else "Primer producto"
            product2 = products[1] if len(products) > 1 else "Segundo producto"
            
            prompt = f"""
Eres un asesor experto que sabe explicar de forma clara y accesible, usando un lenguaje que cualquier persona pueda entender. Tu objetivo es ayudar a tomar la mejor decisión basada en necesidades reales, siendo honesto sobre ventajas y desventajas.

Analiza estos productos:{context_part}

{products_info}

Proporciona un análisis con el siguiente formato usando Markdown:

### 🌟 NUESTRA RECOMENDACIÓN

1. **Recomendación principal:**
  - Para tu caso concreto, te recomendamos [producto] porque [razones clave]

2. **Alternativa a considerar:**
  - Como segunda opción, [otro producto] porque [razones]

### 📊 COMPARATIVA RÁPIDA

**{product1}:**
- Puntos fuertes: [listado]
- Ideal para: [casos de uso]
- Precio/calidad: [valoración]

**{product2}:**
- Puntos fuertes: [listado]
- Ideal para: [casos de uso]
- Precio/calidad: [valoración]

### ✨ DIFERENCIAS CLAVE
- [3-4 diferencias importantes]"""

            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un asesor experto que combina conocimiento profundo con capacidad de explicar de forma simple. Evita tecnicismos innecesarios y céntrate en el valor real para el usuario. Sé honesto sobre ventajas y desventajas."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return {
                "success": True,
                "analysis": response.choices[0].message.content
            }

        except Exception as e:
            print(f"Error en recomendación: {str(e)}")
            return {
                "success": False,
                "error": "No se pudo generar la recomendación. Por favor, intenta de nuevo."
            }

    def analyze_products(self, urls):
        """Función principal para analizar productos"""
        try:
            products_info = []
            
            for url in urls:
                product_description = self.extract_product_info_from_url(url)
                if product_description:
                    # Enriquecer la información con el análisis de IA
                    details = product_description
                    
                    if details:
                        products_info.append({
                            "details": details,
                        })
            
            result = None
            if len(products_info) > 1:
                comparison = self.compare_products("\n\n".join([p["details"] for p in products_info]))
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


def parse_args():
    """Procesa los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Analizar y recomendar productos')
    parser.add_argument('--mode', choices=['compare', 'recommend'], default='compare',
                       help='Modo de operación: comparar o recomendar')
    parser.add_argument('--type', help='Tipo de producto para recomendación')
    parser.add_argument('--min-budget', help='Presupuesto mínimo')
    parser.add_argument('--max-budget', help='Presupuesto máximo')
    parser.add_argument('--use', help='Uso principal')
    parser.add_argument('--needs', help='Necesidades específicas')
    parser.add_argument('urls', nargs='*', help='URLs de productos a comparar')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    analyzer = ProductAnalyzer()
    
    if args.mode == 'recommend':
        try:
            recommendations = analyzer.compare_products(
                args.urls
            )
            
            print("\nRESULT_JSON_START")
            print(json.dumps(recommendations, ensure_ascii=False))
            print("RESULT_JSON_END")
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e)
            }
            print("\nRESULT_JSON_START")
            print(json.dumps(error_result, ensure_ascii=False))
            print("RESULT_JSON_END")
    else:
        analyzer.analyze_products(args.urls)
