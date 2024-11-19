def create_comparison_prompt(product1_data, product2_data):
    """Crea un prompt para OpenAI para comparar dos productos"""
    prompt = """Actúa como un experto en tecnología y análisis de productos. 
    Por favor, compara los siguientes dos productos y proporciona un análisis detallado:

    Producto 1:
    Nombre: {name1}
    Precio: {price1}€
    Especificaciones: {specs1}

    Producto 2:
    Nombre: {name2}
    Precio: {price2}€
    Especificaciones: {specs2}

    Por favor, proporciona:
    1. Una comparación detallada de las características principales
    2. Ventajas y desventajas de cada producto
    3. Relación calidad-precio
    4. Recomendación final basada en el uso típico
    5. ¿Cuál ofrece mejor valor por el dinero?
    
    Responde en español y de manera que sea fácil de entender para un usuario no técnico."""

    return prompt.format(
        name1=product1_data.get('name', 'No disponible'),
        price1=product1_data.get('current_price', 'No disponible'),
        specs1='\n- '.join(product1_data.get('specifications', ['No disponible'])),
        name2=product2_data.get('name', 'No disponible'),
        price2=product2_data.get('current_price', 'No disponible'),
        specs2='\n- '.join(product2_data.get('specifications', ['No disponible']))
    ) 