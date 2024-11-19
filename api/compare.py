from http.server import BaseHTTPRequestHandler
from openai import OpenAI
import json
import re
import os
from urllib.parse import urlparse, unquote

def extract_product_info(url):
    """Extrae información del producto desde la URL sin hacer requests"""
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

    if not product_description:
        product_description = clean_path

    return product_description

def analyze_with_perplexity(products_info):
    """Analiza productos usando Perplexity con un prompt optimizado"""
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
                    "content": "Eres un experto que da consejos claros y prácticos sobre productos. Usa lenguaje natural y enfócate en beneficios reales para el usuario."
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

def handler(event, context):
    """Manejador principal para Vercel"""
    try:
        # Obtener las URLs del body
        body = json.loads(event.get('body', '{}'))
        urls = body.get('urls', [])

        if not urls:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No se proporcionaron URLs'
                })
            }

        # Extraer información de cada URL
        products_info = []
        for url in urls:
            product_info = extract_product_info(url)
            if product_info:
                products_info.append(product_info)

        # Si tenemos información de productos, analizarla
        if products_info:
            analysis = analyze_with_perplexity("\n\n".join(products_info))
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'analysis': analysis
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No se pudo extraer información de los productos'
                })
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Error en el procesamiento: {str(e)}'
            })
        }

def do_OPTIONS(self):
    """Manejo de CORS"""
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    self.end_headers()