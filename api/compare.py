from http.server import BaseHTTPRequestHandler
from openai import OpenAI
import json
import re
import os
from urllib.parse import urlparse, unquote

def extract_product_info(url):
    """Extrae información del producto desde la URL"""
    decoded_url = unquote(url)
    path = urlparse(decoded_url).path
    clean_path = path.replace('-', ' ').replace('_', ' ').replace('/', ' ').lower()
    
    patterns = {
        'brand': r'(samsung|lg|philips|bosch|siemens|balay|whirlpool|apple|hp|lenovo|acer|asus|msi|pccom)',
        'model': r'([a-zA-Z0-9]+-?[a-zA-Z0-9]+)',
        'features': r'(wifi|smart|digital|\d+\s*(gb|tb|inch|pulgadas|\"|cm|kg|w|hz|rtx|rx|gtx|ram|ssd))',
        'category': r'(tv|telefono|portatil|laptop|nevera|lavadora|secadora|monitor|pc|ordenador)'
    }
    
    extracted_info = {}
    for key, pattern in patterns.items():
        matches = re.finditer(pattern, clean_path, re.IGNORECASE)
        extracted_info[key] = list(set([match.group(0) for match in matches]))
    
    product_description = ' '.join([
        item for sublist in extracted_info.values() 
        for item in sublist
    ])

    return product_description or clean_path

def analyze_with_perplexity(products_info):
    """Analiza productos usando Perplexity"""
    try:
        api_key = os.environ.get('PERPLEXITY_API_KEY')
        if not api_key:
            raise ValueError("No se encontró PERPLEXITY_API_KEY")

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )

        prompt = f"""
        Compara estos productos de forma concisa y clara:

        {products_info}

        Estructura la respuesta así:

        ### 🎯 RESUMEN RÁPIDO
        **¿Cuál elegir?** [Una frase clara sobre qué producto es mejor según el uso]

        ### 👤 PERFIL IDEAL
        • Primer producto ideal para:
          - **Usuarios** que [beneficio principal]
          - **Personas** que [ventaja clave]

        • Segundo producto ideal para:
          - **Usuarios** que [beneficio principal]
          - **Personas** que [ventaja clave]

        ### ⚡ DIFERENCIAS CLAVE
        • **Principal:** [diferencia más importante]
        • **Rendimiento:** [comparación de rendimiento]
        • **Precio/Calidad:** [relación calidad-precio]

        ### 💡 CONSEJO FINAL
        [Recomendación directa y personal]
        """

        response = client.chat.completions.create(
            model="llama-3.1-sonar-large-128k-online",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto que da consejos claros y prácticos sobre productos."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error en el análisis: {str(e)}"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            urls = data.get('urls', [])

            if not urls:
                self.send_error(400, "No se proporcionaron URLs")
                return

            products_info = []
            for url in urls:
                info = extract_product_info(url)
                if info:
                    products_info.append(info)

            if not products_info:
                self.send_error(400, "No se pudo extraer información de los productos")
                return

            analysis = analyze_with_perplexity("\n\n".join(products_info))
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                "success": True,
                "analysis": analysis
            })
            
            self.wfile.write(response.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                "error": str(e)
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()