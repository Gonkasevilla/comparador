#!/bin/bash

# Asegurarse de que Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 no encontrado, instalando..."
    apt-get update && apt-get install -y python3 python3-pip
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Instalar dependencias
python3 -m pip install -r requirements.txt

# Ejecutar la aplicación
exec python3 app.py