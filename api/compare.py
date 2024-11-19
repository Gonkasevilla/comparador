from openai import OpenAI
import json
import re
import os
from urllib.parse import urlparse, unquote

def extract_info(url):
    decoded_url = unquote(url)
    path = urlparse(decoded_url).path.lower()
    return ' '.join(word for word in path.replace('-', ' ').split() if len(word) > 2 or word.isdigit())

def analyze(products_info):
    try:
        client = OpenAI(
            api_key=os.environ.get('PERPLEXITY_API_KEY'),
            base_url="https://api.perplexity.ai"
        )

        prompt = f"""
        Compara brevemente:
        {products_info}

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
        [dos líneas máximo]
        """

        response = client.chat.completions.create(
            model="llama-3.1-sonar-large-128k-online",
            messages=[
                {"role": "system", "content": "Da recomendaciones breves y prácticas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def index(req):
    if req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }

    try:
        body = json.loads(req.body)
        urls = body.get('urls', [])

        if not urls:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Se requieren URLs para comparar'
                })
            }

        products_info = [extract_info(url) for url in urls]
        analysis = analyze("\n".join(products_info))

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

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }