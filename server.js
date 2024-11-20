const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
console.log('Iniciando servidor...');

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Estado del servidor
let serverReady = false;

// Health check simplificado
app.get('/health', (req, res) => {
    if (!serverReady) {
        console.log('Health check fallido - servidor no listo');
        return res.status(503).json({ status: 'initializing' });
    }
    console.log('Health check exitoso');
    res.status(200).json({ status: 'healthy' });
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PYTHON_PATH = 'python3';
const ANALYZER_PATH = path.join(__dirname, 'backend', 'scrapers', 'perplexity_analyzer.py');

// Verificar que el archivo existe
if (!fs.existsSync(ANALYZER_PATH)) {
    console.error('ERROR: No se encuentra el archivo del analizador en:', ANALYZER_PATH);
    process.exit(1);
}

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

    try {
        const pythonProcess = spawn(PYTHON_PATH, [ANALYZER_PATH, ...urls], {
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });

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
    } catch (error) {
        console.error('Error al iniciar proceso Python:', error);
        return sendResponse(500, {
            error: 'Error al iniciar el analizador',
            details: error.message
        });
    }
});

const PORT = process.env.PORT || 3000;

// Inicialización en dos fases
const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Servidor iniciado en puerto ${PORT}`);
    
    // Verificar que Python está disponible
    const pythonTest = spawn('python3', ['--version']);
    
    pythonTest.on('close', (code) => {
        if (code === 0) {
            console.log('Python disponible');
            serverReady = true;
        } else {
            console.error('Python no disponible');
            process.exit(1);
        }
    });
});

// Manejo de errores del servidor
server.on('error', (error) => {
    console.error('Error en el servidor:', error);
    process.exit(1);
});

// Manejo de señales
process.on('SIGTERM', () => {
    console.log('SIGTERM recibido');
    server.close(() => {
        console.log('Servidor cerrado');
        process.exit(0);
    });
});