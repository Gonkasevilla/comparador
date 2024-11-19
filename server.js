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

    const pythonProcess = spawn('python3', [  // Cambiado a python3
        path.join(__dirname, 'api', 'compare.py'),  // Cambiada la ruta
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
            let jsonData;
            const markerMatch = outputData.match(/RESULT_JSON_START\n([\s\S]*?)\nRESULT_JSON_END/);
            if (markerMatch) {
                console.log('JSON encontrado entre marcadores');
                jsonData = JSON.parse(markerMatch[1].trim());
            }
            
            if (!jsonData) {
                console.log('Intentando encontrar JSON válido en el texto completo');
                const jsonMatch = outputData.match(/\{[\s\S]*\}/g);
                if (jsonMatch) {
                    jsonData = JSON.parse(jsonMatch[jsonMatch.length - 1]);
                }
            }

            if (!jsonData) {
                throw new Error('No se pudo encontrar un JSON válido en la respuesta');
            }

            res.json(jsonData);

        } catch (error) {
            console.error('Error al procesar la respuesta:', error);
            console.error('Contenido completo de la respuesta:', outputData);
            
            res.status(500).json({
                error: 'Error procesando la comparación',
                details: error.message
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
});