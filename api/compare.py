from openai import OpenAI
import json
import re
import os
from urllib.parse import urlparse, unquote

def extract_product_info(url):
    """Extrae información del producto desde la URL"""
    print(f"Extrayendo info de URL: {url}")  # Debug log
    decoded_url = unquote(url)
    path = urlparse(decoded_url).path
    clean_path = path.replace('-', ' ').replace('_', ' ').replace('/', ' ').lower()
    
    # ... resto del código de extracción ...
    
    print(f"Información extraída: {product_description}")  # Debug log
    return product_description

def analyze_with_perplexity(products_info):
    """Analiza productos usando Perplexity"""
    print("Iniciando análisis con Perplexity")  # Debug log
    try:
        api_key = os.environ.get('PERPLEXITY_API_KEY')
        if not api_key:
            raise ValueError("No se encontró PERPLEXITY_API_KEY")

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )

        print("Enviando prompt a Perplexity")  # Debug log
        response = client.chat.completions.create(
            model="llama-3.1-sonar-large-128k-online",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto que da consejos claros y prácticos sobre productos."
                },
                {
                    "role": "user",
                    "content": f"Compara estos productos de forma concisa:\n\n{products_info}"
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )

        print("Respuesta recibida de Perplexity")  # Debug log
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error en Perplexity: {str(e)}")  # Debug log
        return f"Error en el análisis: {str(e)}"

def handler(request):
    """Manejador principal para Vercel"""
    print("Iniciando handler")  # Debug log
    
    if request.method == "OPTIONS":
        print("Manejando OPTIONS request")  # Debug log
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": ""  # Cuerpo vacío para OPTIONS
        }

    try:
        print(f"Método de la request: {request.method}")  # Debug log
        
        if request.method == "POST":
            print("Procesando POST request")  # Debug log
            
            # Intentar parsear el body
            try:
                body = json.loads(request.body)
                print(f"Body parseado: {body}")  # Debug log
            except json.JSONDecodeError as e:
                print(f"Error parseando JSON: {str(e)}")  # Debug log
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps({
                        "error": f"Error en formato JSON: {str(e)}"
                    })
                }

            urls = body.get('urls', [])
            print(f"URLs recibidas: {urls}")  # Debug log

            if not urls:
                print("No se proporcionaron URLs")  # Debug log
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps({
                        "error": "No se proporcionaron URLs"
                    })
                }

            # Procesar URLs
            products_info = []
            for url in urls:
                info = extract_product_info(url)
                if info:
                    products_info.append(info)

            if products_info:
                print("Analizando productos")  # Debug log
                analysis = analyze_with_perplexity("\n\n".join(products_info))
                
                response = {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps({
                        "success": True,
                        "analysis": analysis
                    })
                }
                print(f"Enviando respuesta: {response}")  # Debug log
                return response

    except Exception as e:
        error_msg = f"Error en el procesamiento: {str(e)}"
        print(f"Error: {error_msg}")  # Debug log
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": error_msg
            })
        }