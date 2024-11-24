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
        """Compara productos con enfoque en uso real y formato mejorado"""
        try:
            prompt = f"""
            Como experto asesor de compras, compara estos productos:

            {products_info}

            Estructura tu respuesta exactamente así:

            ### 🎯 RESUMEN RÁPIDO
            **¿Cuál elegir?** [Una frase clara y directa sobre qué producto es mejor para cada tipo de usuario]

            ### 👤 PERFIL IDEAL
            • El primer producto es perfecto para:
              - **Usuarios** que buscan [beneficio principal]
              - **Personas** que necesitan [ventaja específica]
              - **Ideal** para quienes [característica principal]

            • El segundo producto es perfecto para:
              - **Usuarios** que quieren [beneficio principal]
              - **Personas** que buscan [ventaja específica]
              - **Ideal** para quienes [característica principal]

            ### ⚡ DIFERENCIAS IMPORTANTES
            • **Rendimiento y Velocidad:**
              - Primer producto: [explicar características y beneficios]
              - Segundo producto: [explicar características y beneficios]

            • **Diseño y Calidad:**
              - Primer producto: [explicar características importantes]
              - Segundo producto: [explicar características importantes]

            • **Características Especiales:**
              - Primer producto: [mencionar funciones únicas]
              - Segundo producto: [mencionar funciones únicas]

            ### 💡 CONSEJO PERSONAL
            **Mi recomendación sincera:** [Da un consejo claro sobre qué producto elegir según el tipo de usuario, explicando el porqué de forma natural]
            """

            messages = [
                {
                    "role": "system",
                    "content": """Eres un experto que ayuda a elegir productos.
                    - Usa un tono natural y amigable
                    - Mantén los emojis en los títulos
                    - Usa negritas (**) para destacar puntos clave
                    - Usa viñetas como se indica en el formato
                    - Explica los beneficios prácticos
                    - Da recomendaciones claras y directas"""
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

    def get_recommendations(self, product_type, min_budget, max_budget, main_use, needs):
        """Genera recomendaciones personalizadas"""
        try:
            prompt = f"""
            Actúa como experto asesor de tecnología y encuentra los mejores productos disponibles que cumplan estos requisitos:

            NECESIDADES:
            • Tipo de producto: {product_type}
            • Presupuesto: {min_budget if min_budget else '0'}€ - {max_budget}€
            • Uso principal: {main_use}
            • Necesidades específicas: {needs}

            Recomienda 3 productos reales y actuales usando este formato:

            ### 💫 RECOMENDACIONES PRINCIPALES
            • **La mejor opción:** [producto] porque [razón principal]
            • **Alternativa destacada:** [producto] especialmente si [condición específica]
            • **Opción económica:** [producto] ideal para [caso de uso]

            ### 🎯 ANÁLISIS DETALLADO

            **1. [Nombre del Producto]**
            • **Precio actual:** [precio]€
            • **Puntos fuertes:**
              - [beneficio principal relevante para el usuario]
              - [2-3 características importantes]
            • **Ideal para:** [casos de uso específicos]
            • **Disponible en:** [tiendas principales]

            **2. [Nombre del Producto]**
            [Mismo formato que el anterior]

            **3. [Nombre del Producto]**
            [Mismo formato que el anterior]

            ### 💰 COMPARATIVA DE VALOR
            • [Análisis precio/calidad de las opciones]
            • [Justificación de cada inversión]

            ### 🤝 CONSEJO FINAL
            [Recomendación personalizada basada en el perfil exacto del usuario]
            """

            messages = [
                {
                    "role": "system",
                    "content": """Eres un experto en tecnología que recomienda productos de forma práctica y natural.
                    - Usa lenguaje cercano y comprensible
                    - Recomienda solo productos reales y disponibles en España
                    - Mantén recomendaciones dentro del presupuesto
                    - Prioriza beneficios prácticos sobre especificaciones técnicas
                    - Incluye precios actuales aproximados
                    - Da nombres específicos de tiendas donde comprar"""
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
            print(f"Error en recomendaciones: {str(e)}")
            return None
    def analyze_products(self, urls):
        """Función principal para analizar productos"""
        try:
            products_info = []
            
            for url in urls:
                product_description = self.extract_product_info_from_url(url)
                if product_description:
                    details = self.search_product_info(product_description)
                    image_url = self.try_get_product_image(url)
                    if details:
                        products_info.append({
                            "details": details,
                            "image": image_url
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

# Código fuera de la clase para el manejo de argumentos y ejecución
def parse_args():
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
            recommendations = analyzer.get_recommendations(
                args.type,
                args.min_budget,
                args.max_budget,
                args.use,
                args.needs
            )
            
            result = {
                "success": True if recommendations else False,
                "recommendations": recommendations if recommendations else "No se pudieron generar recomendaciones"
            }
            
            print("\nRESULT_JSON_START")
            print(json.dumps(result, ensure_ascii=False))
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