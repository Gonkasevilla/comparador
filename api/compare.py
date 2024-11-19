from http.server import BaseHTTPRequestHandler
from openai import OpenAI
import json
import re
import os
from urllib.parse import urlparse, unquote

def extract_product_info(url):
    """Extrae información rápida del producto desde la URL"""
    decoded_url = unquote(url)
    path = urlparse(decoded_url).path.lower()
    path = path.replace('-', ' ').replace('_', ' ').replace('/', ' ')

    # Extracción más rápida y directa
    relevant_terms = []
    for word in path.split():
        if len(word) > 2 or word.isdigit():  # Solo términos relevantes
            relevant_terms.append(word)

    return ' '.join(relevant_terms)

def create_comparison_prompt(products):
    return f"""Compara brevemente:
{products}

### 🎯 RESUMEN
¿Cuál elegir? [una línea]

### 👤 USOS
• Producto 1: [dos líneas]
• Producto 2: [dos líneas]

### ⚡ DIFERENCIAS
• Principal: [una línea]
• Rendimiento: [una línea]
• Precio/Calidad: [una línea]

### 💡 CONSEJO
[dos líneas máximo]"""

def analyze_with_perplexity(products_info):
    """Análisis rápido con Perplexity"""
    try:
        client = OpenAI(
            api_key=os.environ.get('PERPLEXITY_API_KEY'),
            base_url="https://api.perplexity.ai"
        )

        response = client.chat.completions.create(
            model="llama-3.1-sonar-large-128k-online",
            messages=[
                {"role": "system", "content": "Da recomendaciones breves y prácticas."},
                {"role": "user", "content": create_comparison_prompt(products_info)}
            ],
            temperature=0.3,
            max_tokens=500  # Reducido para respuestas más cortas
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def handle_request(event, context):
    """Manejador principal optimizado"""
    try:
        # Parsear body
        body = json.loads(event.get('body', '{}'))
        urls = body.get('urls', [])

        if not urls:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'URLs requeridas'})
            }

        # Extraer información rápidamente
        products_info = [extract_product_info(url) for url in urls]
        
        # Análisis rápido
        analysis = analyze_with_perplexity("\n".join(products_info))

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': True, 'analysis': analysis})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

# Handler para Vercel
def handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    return handle_request(event, context)