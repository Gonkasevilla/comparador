from http.server import BaseHTTPRequestHandler
from openai import OpenAI
import json
import re
import os
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup

class ProductAnalyzer:
    def __init__(self):
        self.api_key = os.environ.get('PERPLEXITY_API_KEY')
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
        parsed_url = urlparse(decoded_url)
        domain = parsed_url.netloc
        path = parsed_url.path
        clean_path = path.replace('-', ' ').replace('_', ' ').replace('/', ' ').lower()

        # Manejo específico por tienda
        if 'carrefour.es' in domain:
            product_name_match = re.search(r'/([^/]+)/[^/]+/p$', path)
            if product_name_match:
                clean_path = product_name_match.group(1).replace('-', ' ')
                clean_path = ' '.join(word.capitalize() for word in clean_path.split())
        
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
        
        if 'carrefour.es' in domain:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title_element = soup.select_one('h1.product-title')
                    if title_element:
                        clean_path = title_element.text.strip()
            except Exception as e:
                print(f"Error obteniendo información adicional: {str(e)}")
        
        product_description = ' '.join([
            item for sublist in extracted_info.values() 
            for item in sublist
        ])

        if not product_description and clean_path:
            product_description = clean_path

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
              - **Gamers** que valoran [característica principal]
              - **Usuarios** que buscan [beneficio principal]
              - **Personas** que necesitan [ventaja específica]

            • El segundo producto es perfecto para:
              - **Gamers** que prefieren [característica principal]
              - **Usuarios** que quieren [beneficio principal]
              - **Personas** que buscan [ventaja específica]

            ### ⚡ DIFERENCIAS IMPORTANTES
            • **Rendimiento y Velocidad:**
              - El primer producto: [explicar características y beneficios]
              - El segundo producto: [explicar características y beneficios]

            • **Diseño y Calidad:**
              - El primer producto: [explicar características importantes]
              - El segundo producto: [explicar características importantes]

            • **Características Especiales:**
              - El primer producto: [mencionar funciones únicas]
              - El segundo producto: [mencionar funciones únicas]

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

def analyze_products(urls):
    """Función principal para analizar productos"""
    try:
        analyzer = ProductAnalyzer()
        products_info = []
        
        for url in urls:
            product_description = analyzer.extract_product_info_from_url(url)
            if product_description:
                details = analyzer.search_product_info(product_description)
                if details:
                    products_info.append({
                        "details": details,
                        "image": None
                    })
        
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
                "analysis": products_info[0]["details"]
            }
        else:
            result = {
                "success": False,
                "error": "No se pudo obtener información de los productos"
            }
        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        try:
            result = analyze_products(data.get('urls', []))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                "error": str(e)
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()