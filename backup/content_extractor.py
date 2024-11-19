from playwright.sync_api import sync_playwright
import json
import sys
import re
from typing import Dict, List

class ProductExtractor:
    def __init__(self):
        # Patrones de precio actualizados
        self.price_patterns = [
            r'(\d+[.,]\d{2})\s*€',       # 1.059,00 € o 1059,00 €
            r'(\d+)[.,](\d{2})\s*€',      # Separado en grupos
            r'(\d+)\s*€',                 # Precio sin decimales
            r'PVP\s*(\d+[.,]\d{2})\s*€'  # Precio con PVP delante
        ]
        
        # Palabras clave específicas para TVs
        self.tv_keywords = [
            'pulgadas', 'resolución', 'uhd', '4k', 'hdr', 'smart tv', 
            'hz', 'hdmi', 'usb', 'wifi', 'bluetooth', 'sistema operativo',
            'pantalla', 'panel', 'sonido', 'dolby', 'procesador', 
            'dimensiones', 'vesa', 'consumo', 'clase energética'
        ]
        
        # Palabras para excluir
        self.exclude_keywords = [
            'cookies', 'menú', 'inicio', 'cuenta', 'carrito', 'envío',
            'devolución', 'garantía', 'política', 'privacidad', 'login',
            'registro', 'ayuda', 'soporte', 'contacto', 'newsletter',
            'redes sociales', 'síguenos'
        ]

    def clean_price(self, text: str) -> float:
        """Limpia y extrae el precio"""
        if not text:
            return None
            
        # Eliminar espacios y caracteres no deseados
        text = text.replace('\u202f', ' ').strip()
            
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1)
                price_str = price_str.replace('.', '').replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        return None

    def is_valid_feature(self, text: str) -> bool:
        """Determina si el texto es una característica válida de TV"""
        text = text.lower()
        
        # Validaciones básicas
        if not text or len(text) < 5 or len(text) > 200:
            return False
            
        # Excluir elementos de navegación y menú
        if any(word in text for word in self.exclude_keywords):
            return False
            
        # Incluir si contiene palabras clave de TV
        if any(keyword in text for keyword in self.tv_keywords):
            return True
            
        # Patrones comunes de características
        if ':' in text and not ('http:' in text or 'www:' in text):
            return True
            
        # Características que empiezan con guion o bullet
        if text.strip('- •').strip() and len(text) > 10:
            return True
            
        return False

    def extract_product_info(self, url: str) -> Dict:
        """Extrae información del producto"""
        print(f"\nExtrayendo información de: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                print("Página cargada. Extrayendo información...")
                
                content = page.evaluate("""() => {
                    function getText(element) {
                        return element ? element.textContent.trim() : '';
                    }
                    
                    // Buscar título
                    const title =
                        getText(document.querySelector('h1')) ||
                        getText(document.querySelector('[class*="title"]')) ||
                        getText(document.querySelector('[class*="product-name"]'));
                    
                    // Buscar precios
                    const prices = Array.from(
                        document.querySelectorAll('[class*="price"], [class*="Price"], [class*="amount"], .pvpr')
                    ).map(el => getText(el));
                    
                    // Buscar características
                    const features = new Set();
                    
                    // En listas
                    document.querySelectorAll('ul li, ol li, dl dt, dl dd').forEach(el => {
                        const text = getText(el);
                        if (text) features.add(text);
                    });
                    
                    // En tablas
                    document.querySelectorAll('table tr').forEach(row => {
                        const cells = row.querySelectorAll('td, th');
                        if (cells.length >= 2) {
                            features.add(`${getText(cells[0])}: ${getText(cells[1])}`);
                        }
                    });
                    
                    // En secciones específicas
                    [
                        '[class*="feature"]',
                        '[class*="spec"]',
                        '[class*="detail"]',
                        '[class*="description"]',
                        '[class*="caracteristica"]',
                        '[class*="tecnolog"]'
                    ].forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            const text = getText(el);
                            if (text) features.add(text);
                        });
                    });
                    
                    return {
                        title,
                        prices,
                        features: Array.from(features)
                    };
                """)
                
                # Procesar la información extraída
                product_info = {
                    'title': content['title'].strip(),
                    'features': []
                }
                
                # Procesar precios
                prices = []
                for price_text in content['prices']:
                    price = self.clean_price(price_text)
                    if price and price > 100:  # Filtrar precios irrelevantes
                        prices.append(price)
                
                if prices:
                    prices = sorted(prices)
                    product_info['current_price'] = prices[0]
                    if len(prices) > 1 and prices[-1] > prices[0]:
                        product_info['original_price'] = prices[-1]
                
                # Procesar características
                features = []
                for feature in content['features']:
                    if self.is_valid_feature(feature):
                        features.append(feature.strip())
                
                # Eliminar duplicados manteniendo el orden
                features = list(dict.fromkeys(features))
                product_info['features'] = features
                
                # Formatear para el prompt
                formatted_content = f"""
PRODUCTO: {product_info['title']}
PRECIO ACTUAL: {product_info.get('current_price', 'No disponible')}€
{f"PRECIO ORIGINAL: {product_info.get('original_price')}€" if 'original_price' in product_info else ""}

CARACTERÍSTICAS PRINCIPALES:
{chr(10).join(f"- {feature}" for feature in features[:15] if len(feature) > 5)}
"""
                print("Información extraída exitosamente")
                return {
                    'success': True,
                    'content': formatted_content.strip(),
                    'raw_data': product_info
                }
                
            except Exception as e:
                print(f"Error: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'url': url
                }
            finally:
                browser.close()

def compare_products(urls: List[str]) -> str:
    extractor = ProductExtractor()
    results = []
    
    for url in urls:
        result = extractor.extract_product_info(url)
        if result['success']:
            results.append(result['content'])
    
    if results:
        prompt = """Por favor, analiza estos televisores y proporciona:
1. Comparación de especificaciones clave (tamaño, resolución, tecnología de panel, etc.)
2. Análisis de características smart TV y conectividad
3. Comparación de calidad de imagen y sonido
4. Relación calidad-precio
5. Recomendación final basada en diferentes casos de uso (gaming, películas, uso general)

TELEVISORES A COMPARAR:
"""
        return prompt + "\n\n---\n\n".join(results)
    else:
        return "No se pudo extraer información de los productos."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Por favor proporciona al menos una URL")
        sys.exit(1)
    
    urls = sys.argv[1:]
    prompt = compare_products(urls)
    print("\nPrompt generado:")
    print(prompt)