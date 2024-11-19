from scraper import extract_product_info
from comparison import create_comparison_prompt
import openai

# Configurar OpenAI
openai.api_key = 'tu_api_key'

def compare_products(url1, url2):
    # Extraer información de ambos productos
    product1_data = extract_product_info(url1)
    product2_data = extract_product_info(url2)
    
    if not product1_data['success'] or not product2_data['success']:
        return "Error: No se pudo extraer la información de uno o ambos productos"
    
    # Crear el prompt
    prompt = create_comparison_prompt(product1_data, product2_data)
    
    # Obtener la comparación de OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un experto en análisis y comparación de productos tecnológicos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

# Uso
url1 = "URL_del_primer_producto"
url2 = "URL_del_segundo_producto"
comparison = compare_products(url1, url2)
print(comparison) 