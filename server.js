const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const runPythonComparison = (urls) => {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python3', [
            path.join(__dirname, 'server.py'),  // Usamos el nuevo server.py
            ...urls
        ]);

        let outputData = '';

        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error('Error de Python:', data.toString());
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(`Proceso terminado con código ${code}`));
                return;
            }

            try {
                // Intentar extraer el JSON de la salida
                const jsonMatch = outputData.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    const result = JSON.parse(jsonMatch[0]);
                    resolve(result);
                } else {
                    reject(new Error('No se encontró JSON en la respuesta'));
                }
            } catch (error) {
                reject(error);
            }
        });

        pythonProcess.on('error', (error) => {
            reject(error);
        });
    });
};

app.post('/api/compare', async (req, res) => {
    try {
        const { urls } = req.body;
        
        if (!urls || !Array.isArray(urls) || urls.length < 1) {
            return res.status(400).json({ 
                error: 'Se requieren URLs para comparar' 
            });
        }

        console.log('Comparando productos:', urls);

        const result = await runPythonComparison(urls);
        res.json(result);

    } catch (error) {
        console.error('Error en la comparación:', error);
        res.status(500).json({
            error: 'Error procesando la comparación',
            details: error.message
        });
    }
});

// Ruta de health check para Railway
app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

// Manejo de errores general
app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({
        error: 'Error interno del servidor',
        details: err.message
    });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Servidor corriendo en http://0.0.0.0:${PORT}`);
    console.log('Para acceder localmente: http://localhost:${PORT}');
});