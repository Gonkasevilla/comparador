from playwright.sync_api import sync_playwright
import json
import sys
import re
from urllib.parse import urlparse

def clean_price(price_str):
    """Limpia y convierte el precio a formato correcto"""
    try:
        # Eliminar el símbolo de euro y espacios
        price_str = price_str.replace('€', '').strip()
        
        # Si tiene punto y coma, es un formato especial
        if '.' in price_str and ',' in price_str:
            price_str = price_str.replace('.', '').replace(',', '.')
        elif '.' in price_str:
            price_str = price_str.replace('.', '')
        elif ',' in price_str:
            price_str = price_str.replace(',', '.')
        
        price = float(price_str)
        return price if price > 0 else None
    except:
        return None

def extract_product_info(url):
    """Extrae la información esencial del producto para comparación"""
    print("Iniciando extracción...")
    
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            )
            page = context.new_page()
            page.set_default_timeout(30000)
            
            response = page.goto(url, wait_until='domcontentloaded')
            page.wait_for_selector('h1', timeout=10000)

            product_data = {
                'url': url,
                'success': False
            }

            # Extraer nombre del producto
            name_element = page.locator('h1').first
            if name_element:
                product_data['name'] = name_element.text_content().strip()

            # Extraer descripción o características principales
            try:
                # Intentar obtener la descripción del producto
                description = page.locator('.description, .specifications, .features').first
                if description:
                    product_data['description'] = description.text_content().strip()
            except:
                product_data['description'] = ""

            # Extraer especificaciones técnicas
            try:
                specs = []
                specs_elements = page.locator('.specifications li, .tech-specs li, .features li').all()
                for spec in specs_elements[:10]:  # Limitamos a 10 especificaciones principales
                    specs.append(spec.text_content().strip())
                product_data['specifications'] = specs
            except:
                product_data['specifications'] = []

            # Extraer precio actual
            found_prices = []
            price_patterns = [
                r'(\d+\.?\d*,\d{2})\s*€',
                r'(\d+,\d{2})\s*€',
                r'(\d+)\s*€'
            ]
            
            html_content = page.content()
            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    clean_price_value = clean_price(match)
                    if clean_price_value and clean_price_value > 0:
                        found_prices.append(clean_price_value)
            
            if found_prices:
                found_prices.sort()
                product_data['current_price'] = found_prices[0]

            # Marcar como exitoso si tenemos los datos mínimos necesarios
            product_data['success'] = all(key in product_data for key in ['name', 'current_price'])
            
            return product_data

        except Exception as e:
            print(f"Error durante la extracción: {str(e)}")
            return {
                'error': str(e),
                'url': url,
                'success': False
            }
        finally:
            if browser:
                browser.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'URL no proporcionada', 'success': False}))
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"Iniciando proceso para URL: {url}")
    result = extract_product_info(url)
    print("\nResultado final:")
    print(json.dumps(result, ensure_ascii=False, indent=2))