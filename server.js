const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.post('/api/compare', async (req, res) => {
    const { urls } = req.body;
    
    if (!urls || !Array.isArray(urls) || urls.length < 1) {
        return res.status(400).json({ error: 'Se requiere al menos una URL' });
    }

    console.log('Analizando URLs:', JSON.stringify(urls, null, 2));

    const pythonProcess = spawn('python', [
        path.join(__dirname, 'backend', 'scrapers', 'perplexity_analyzer.py'),
        ...urls
    ]);

    let outputData = '';

    pythonProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        console.log('Recibiendo datos:', chunk);
        outputData += chunk;
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error('Error de Python:', data.toString());
    });

    pythonProcess.on('close', (code) => {
        console.log('Código de salida Python:', code);
        console.log('Datos completos recibidos:\n', outputData);

        try {
            // Intentar diferentes métodos para encontrar el JSON
            let jsonData;
            
            // Método 1: Buscar entre marcadores
            const markerMatch = outputData.match(/RESULT_JSON_START\n([\s\S]*?)\nRESULT_JSON_END/);
            if (markerMatch) {
                console.log('JSON encontrado entre marcadores');
                jsonData = JSON.parse(markerMatch[1].trim());
            }
            
            // Método 2: Buscar el último objeto JSON válido en el texto
            if (!jsonData) {
                console.log('Intentando encontrar JSON válido en el texto completo');
                const jsonMatch = outputData.match(/\{[\s\S]*\}/g);
                if (jsonMatch) {
                    console.log('Encontrado posible JSON en el texto');
                    jsonData = JSON.parse(jsonMatch[jsonMatch.length - 1]);
                }
            }

            if (!jsonData) {
                throw new Error('No se pudo encontrar un JSON válido en la respuesta');
            }

            console.log('JSON procesado exitosamente');
            res.json(jsonData);

        } catch (error) {
            console.error('Error al procesar la respuesta:', error);
            console.error('Contenido completo de la respuesta:', outputData);
            
            res.status(500).json({
                error: 'Error procesando la comparación',
                details: error.message,
                debugInfo: {
                    outputLength: outputData.length,
                    firstLines: outputData.split('\n').slice(0, 5),
                    lastLines: outputData.split('\n').slice(-5)
                }
            });
        }
    });

    pythonProcess.on('error', (error) => {
        console.error('Error al ejecutar Python:', error);
        res.status(500).json({
            error: 'Error al ejecutar el analizador',
            details: error.message
        });
    });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Servidor corriendo en http://localhost:${PORT}`);
    console.log('Logs detallados activados');
});