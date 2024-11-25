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
        """Compara productos usando IA"""
        try:
            context_part = f"\nTeniendo en cuenta que el usuario busca: {user_context}" if user_context else ""
            
            prompt = f"""
            Actúa como un experto asesor de tecnología y analiza estos productos:{context_part}

            {products_info}

            Proporciona un análisis detallado con este formato:

            💡 RECOMENDACIÓN RÁPIDA
            • **La mejor opción es** [producto] porque [razón principal]
            • **También podrías considerar** [otro producto] si [condición específica]

            👤 PERFILES DE USO
            **Primer producto es ideal para:**
            • Usuarios que [beneficio principal]
            • Personas que [ventaja específica]
            • Casos donde [característica importante]

            **Segundo producto es ideal para:**
            • Usuarios que [beneficio principal]
            • Personas que [ventaja específica]
            • Casos donde [característica importante]

            📊 COMPARATIVA DETALLADA
            • **Rendimiento:** [comparación clara]
            • **Calidad/Precio:** [análisis de valor]
            • **Características:** [diferencias clave]
            • **Ventajas/Desventajas:** [puntos importantes]

            💰 ANÁLISIS DE PRECIO
            • **Primer producto:** [valor por dinero]
            • **Segundo producto:** [valor por dinero]
            • **Comparativa:** [análisis de la inversión]

            🎯 CONSEJO FINAL
            [Recomendación personalizada considerando el contexto y necesidades del usuario]
            """

            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto asesor de tecnología que habla de forma natural 
                        y cercana. Tu objetivo es ayudar a los usuarios a tomar la mejor decisión de 
                        compra basada en sus necesidades específicas."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error en comparación: {str(e)}")
            return None
 def get_recommendations(self, product_type, min_budget, max_budget, main_use, specific_needs):
        """Genera recomendaciones personalizadas"""
        try:
            prompt = f"""
            Actúa como un experto asesor de tecnología en España. 
            Necesito recomendaciones reales y actualizadas para:

            📝 REQUISITOS:
            • Producto: {product_type}
            • Presupuesto: {min_budget}€ - {max_budget}€
            • Uso principal: {main_use}
            • Necesidades: {specific_needs}

            Proporciona un análisis con este formato:

            🏆 TOP 3 RECOMENDACIONES:
            Para cada producto incluir:
            • Nombre exacto del modelo
            • Precio actual aproximado
            • Dónde comprarlo (PCComponentes, MediaMarkt, Amazon España)
            • Por qué es ideal para este uso
            • Características relevantes

            💡 ANÁLISIS POR PERFIL:
            • Mejor calidad/precio: [Producto] porque [razones]
            • Opción premium: [Producto] porque [razones]
            • Opción equilibrada: [Producto] porque [razones]

            ⚡ COMPARATIVA:
            • Rendimiento: [aspectos clave]
            • Calidad: [construcción y materiales]
            • Durabilidad: [vida útil esperada]
            • Valor: [justificación del precio]

            🎯 RECOMENDACIÓN FINAL:
            • Producto más recomendado
            • Justificación clara
            • Consideraciones importantes
            • Alternativas si el presupuesto es flexible
            """

            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-large-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en tecnología en España. 
                        Proporciona recomendaciones prácticas basadas en productos realmente 
                        disponibles. Usa un lenguaje natural y cercano."""
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
            recommendations = analyzer.get_recommendations(
                args.type,
                args.min_budget,
                args.max_budget,
                args.use,
                args.needs
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