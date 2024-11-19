from playwright.sync_api import sync_playwright
import json
import sys
import re

class ProductScraper:
    def __init__(self):
        self.timeout = 30000
        self.min_price = 1
        self.max_features = 10

    def clean_price(self, text):
        """Limpia y extrae un precio del texto"""
        if not text:
            return None
        match = re.search(r'(\d+[.,]\d{2}|\d+)\s*€', text)
        if match:
            price = float(match.group(1).replace('.', '').replace(',', '.'))
            return price if price > self.min_price else None
        return None

    def extract_info(self, url):
        """Extrae información básica del producto"""
        print(f"Extrayendo información de: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Cargar página
                page.goto(url, timeout=self.timeout)
                page.wait_for_selector('h1', timeout=5000)
                
                # Extraer información básica
                product_info = {
                    'success': False,
                    'url': url,
                    'name': '',
                    'current_price': None,
                    'original_price': None,
                    'features': [],
                    'error': None
                }

                # 1. Nombre del producto
                title_element = page.query_selector('h1')
                if title_element:
                    product_info['name'] = title_element.text_content().strip()
                    print(f"Nombre encontrado: {product_info['name']}")

                # 2. Precios
                prices = []
                price_elements = page.query_selector_all('[class*="price"], .pvp, [data-price]')
                for element in price_elements:
                    price = self.clean_price(element.text_content())
                    if price:
                        prices.append(price)

                if prices:
                    prices.sort()
                    product_info['current_price'] = prices[0]
                    if len(prices) > 1:
                        product_info['original_price'] = prices[-1]
                    print(f"Precio actual: {product_info['current_price']}€")
                    if product_info['original_price']:
                        print(f"Precio original: {product_info['original_price']}€")

                # 3. Características
                feature_elements = page.query_selector_all('li, [class*="feature"], [class*="spec"]')
                features = set()
                
                for element in feature_elements:
                    text = element.text_content().strip()
                    if (len(text) > 10 and 
                        (':' in text or text.startswith('-') or text.startswith('•')) and
                        not any(word in text.lower() for word in [
                            'cookie', 'menú', 'inicio', 'carrito', 'cuenta', 
                            'login', 'regístrate', 'perfil'
                        ])):
                        features.add(text)

                product_info['features'] = list(features)[:self.max_features]
                print(f"Características encontradas: {len(product_info['features'])}")

                # Determinar si la extracción fue exitosa
                product_info['success'] = bool(
                    product_info['name'] and 
                    (product_info['current_price'] or product_info['features'])
                )

                return product_info

            except Exception as e:
                print(f"Error: {str(e)}")
                return {
                    'success': False,
                    'url': url,
                    'error': str(e)
                }
            finally:
                browser.close()

    def format_for_gpt(self, product_info):
        """Formatea la información para enviar a GPT"""
        if not product_info['success']:
            return f"""
Por favor, busca información sobre este producto: {product_info.get('name', 'Producto no identificado')}
URL: {product_info['url']}

No he podido extraer información directamente de la web. 
Por favor, usa tu conocimiento para proporcionar:
1. Características principales del producto
2. Rango de precios habitual
3. Ventajas y desventajas
4. Casos de uso recomendados
"""
        
        return f"""
PRODUCTO: {product_info['name']}

PRECIOS:
- Actual: {product_info['current_price']}€
{f"- Original: {product_info['original_price']}€" if product_info['original_price'] else ""}

CARACTERÍSTICAS ENCONTRADAS:
{chr(10).join(f"- {feature}" for feature in product_info['features'])}

Por favor, analiza esta información y proporciona:
1. Resumen de las características principales
2. Análisis del precio (si es competitivo)
3. Ventajas y desventajas
4. Recomendación según diferentes casos de uso
"""

def compare_products(urls):
    """Compara múltiples productos"""
    scraper = ProductScraper()
    products_info = []
    
    for url in urls:
        info = scraper.extract_info(url)
        products_info.append(scraper.format_for_gpt(info))
    
    prompt = """Por favor, compara los siguientes productos:

1. Analiza las características principales de cada uno
2. Compara precios y relación calidad-precio
3. Identifica ventajas y desventajas de cada uno
4. Proporciona una recomendación según diferentes necesidades o casos de uso

PRODUCTOS A COMPARAR:

"""
    
    return prompt + "\n---\n".join(products_info)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Proporciona al menos una URL")
        sys.exit(1)
    
    prompt = compare_products(sys.argv[1:])
    print("\nPrompt generado para GPT:")
    print(prompt)