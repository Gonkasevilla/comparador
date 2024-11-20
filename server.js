const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.post('/api/compare', async (req, res) => {
    let hasResponded = false;
    const sendResponse = (statusCode, data) => {
        if (!hasResponded) {
            hasResponded = true;
            res.status(statusCode).json(data);
        }
    };

    const { urls } = req.body;
    
    if (!urls || !Array.isArray(urls) || urls.length < 1) {
        return sendResponse(400, { error: 'Se requiere al menos una URL' });
    }

    console.log('Analizando URLs:', JSON.stringify(urls, null, 2));

    // Intentar diferentes comandos de Python
    const pythonCommands = ['python3', 'python', '/usr/bin/python3', '/usr/bin/python'];
    let pythonProcess = null;
    let commandFound = false;

    for (const cmd of pythonCommands) {
        try {
            pythonProcess = spawn(cmd, [
                path.join(__dirname, 'backend', 'scrapers', 'perplexity_analyzer.py'),
                ...urls
            ]);
            commandFound = true;
            console.log(`Usando comando Python: ${cmd}`);
            break;
        } catch (error) {
            console.log(`Comando ${cmd} no disponible:`, error.message);
        }
    }

    if (!commandFound || !pythonProcess) {
        return sendResponse(500, { 
            error: 'Python no encontrado en el sistema',
            details: 'No se pudo encontrar una instalación válida de Python'
        });
    }

    let outputData = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        console.log('Recibiendo datos:', chunk);
        outputData += chunk;
    });

    pythonProcess.stderr.on('data', (data) => {
        const chunk = data.toString();
        console.error('Error de Python:', chunk);
        errorOutput += chunk;
    });

    pythonProcess.on('close', (code) => {
        console.log('Código de salida Python:', code);
        console.log('Datos completos recibidos:\n', outputData);

        try {
            let jsonData;
            const markerMatch = outputData.match(/RESULT_JSON_START\n([\s\S]*?)\nRESULT_JSON_END/);
            
            if (markerMatch) {
                jsonData = JSON.parse(markerMatch[1].trim());
            } else {
                const jsonMatch = outputData.match(/\{[\s\S]*\}/g);
                if (jsonMatch) {
                    jsonData = JSON.parse(jsonMatch[jsonMatch.length - 1]);
                }
            }

            if (jsonData) {
                return sendResponse(200, jsonData);
            } else {
                return sendResponse(500, {
                    error: 'No se pudo encontrar JSON válido en la respuesta',
                    details: errorOutput || 'Sin detalles disponibles'
                });
            }
        } catch (error) {
            return sendResponse(500, {
                error: 'Error procesando la comparación',
                details: error.message,
                errorOutput
            });
        }
    });

    pythonProcess.on('error', (error) => {
        console.error('Error al ejecutar Python:', error);
        return sendResponse(500, {
            error: 'Error al ejecutar el analizador',
            details: error.message
        });
    });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Servidor corriendo en puerto ${PORT}`);
    console.log('Entorno:', process.env.RAILWAY_ENVIRONMENT || 'local');
});