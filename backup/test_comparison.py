from scraper import extract_product_info
from comparison import create_comparison_prompt
import openai

# Configura tu API key de OpenAI
openai.api_key = 'tu_api_key_aquí'

def test_comparison():
    # URLs de ejemplo de PCComponentes
    url1 = "https://www.pccomponentes.com/pccom-ready-amd-ryzen-7-5800x-32gb-1tb-ssd-rtx-4060-ti"
    url2 = "https://www.pccomponentes.com/hp-victus-16-r0053ns-intel-core-i5-13500h-16gb-512gb-ssd-rtx-4050-16-1"
    
    print("Extrayendo información del primer producto...")
    product1 = extract_product_info(url1)
    
    print("\nExtrayendo información del segundo producto...")
    product2 = extract_product_info(url2)
    
    if product1['success'] and product2['success']:
        print("\nCreando comparación...")
        prompt = create_comparison_prompt(product1, product2)
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en análisis y comparación de productos tecnológicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        print("\nComparación:")
        print(response.choices[0].message.content)
    else:
        print("\nError: No se pudo extraer la información de uno o ambos productos")
        if not product1['success']:
            print("Error en producto 1:", product1.get('error'))
        if not product2['success']:
            print("Error en producto 2:", product2.get('error'))

if __name__ == "__main__":
    test_comparison() 