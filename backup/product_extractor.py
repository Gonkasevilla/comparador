from playwright.sync_api import sync_playwright
import json
import sys
import re

def extract_basic_info(url: str):
    """Extrae solo nombre, precio y características básicas"""
    print(f"\nExtrayendo información de: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Cargar página con timeout generoso
            page.goto(url, timeout=30000)
            print("Página cargada")
            
            # Esperar a que cargue el contenido principal
            page.wait_for_selector('h1', timeout=5000)
            
            # Extraer solo lo básico
            product_info = {
                'name': page.query_selector('h1').text_content().strip(),
                'prices': [],
                'specs': []
            }
            
            print(f"Nombre encontrado: {product_info['name']}")
            
            # Buscar precios (actual y original si existe)
            price_elements = page.query_selector_all('[class*="price"], [class*="Price"]')
            for element in price_elements:
                text = element.text_content()
                price_match = re.search(r'(\d+[.,]\d{2}|\d+)\s*€', text)
                if price_match:
                    price = float(price_match.group(1).replace('.', '').replace(',', '.'))
                    if price > 0:
                        product_info['prices'].append(price)
            
            if product_info['prices']:
                print(f"Precios encontrados: {product_info['prices']}")
            
            # Buscar especificaciones básicas
            specs_elements = page.query_selector_all('li')
            for element in specs_elements:
                text = element.text_content().strip()
                if (len(text) > 10 and 
                    (':' in text or text.startswith('-')) and 
                    not any(x in text.lower() for x in ['cookie', 'menú', 'inicio'])):
                    product_info['specs'].append(text)
            
            print(f"Especificaciones encontradas: {len(product_info['specs'])}")
            # Formatear la salida
            formatted = f"""
Producto: {product_info['name']}
Precio actual: {min(product_info['prices']) if product_info['prices'] else 'No disponible'}€
{f"Precio original: {max(product_info['prices'])}€" if len(product_info['prices']) > 1 else ''}

Especificaciones principales:
{chr(10).join(f"- {spec}" for spec in product_info['specs'][:5])}
"""
            return formatted.strip()
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return f"Error extrayendo información: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Proporciona al menos una URL")
        sys.exit(1)
    
    urls = sys.argv[1:]
    results = []
    
    for url in urls:
        info = extract_basic_info(url)
        print("\nInformación extraída:")
        print(info)
        results.append(info)
    
    if len(results) > 1:
        print("\nComparación:")
        print("=============")
        print("\n\n".join(results))