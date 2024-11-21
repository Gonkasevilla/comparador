const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

// Verificar Python al inicio
const verifyPython = () => {
    return new Promise((resolve, reject) => {
        const pythonCheck = spawn('python3', ['--version']);
        pythonCheck.on('close', (code) => {
            if (code === 0) {
                console.log('✅ Python verificado correctamente');
                resolve();
            } else {
                reject(new Error('❌ Python no está disponible'));
            }
        });
    });
};

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Health check
app.get('/health', (_, res) => res.send('OK'));

// Ruta raíz
app.get('/', (_, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API route
app.post('/api/compare', (req, res) => {
    const { urls, userContext } = req.body;
    let hasResponded = false;

    if (!urls || !Array.isArray(urls)) {
        return res.status(400).json({ error: 'URLs inválidas' });
    }

    console.log('📊 Analizando productos con contexto:', userContext || 'Sin contexto');

    const pythonArgs = [
        path.join(__dirname, 'perplexity_analyzer.py'),
        ...urls
    ];
    
    if (userContext) {
        pythonArgs.push('--context');
        pythonArgs.push(userContext);
    }

    const pythonProcess = spawn('python3', pythonArgs);
    let data = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', chunk => {
        const chunkStr = chunk.toString();
        console.log('📥 Recibiendo datos:', chunkStr);
        data += chunkStr;
    });

    pythonProcess.stderr.on('data', error => {
        const errorStr = error.toString();
        console.error('❌ Error de Python:', errorStr);
        errorOutput += errorStr;
    });

    // Manejar timeout
    const timeout = setTimeout(() => {
        if (!hasResponded) {
            hasResponded = true;
            pythonProcess.kill();
            res.status(504).json({ 
                error: 'El análisis ha tardado demasiado tiempo',
                details: 'Timeout de 30 segundos excedido'
            });
        }
    }, 30000);

    pythonProcess.on('close', code => {
        clearTimeout(timeout);
        console.log('📋 Código de salida Python:', code);

        if (hasResponded) return;

        try {
            const match = data.match(/RESULT_JSON_START\n([\s\S]*?)\nRESULT_JSON_END/);
            if (!match) {
                throw new Error('No se pudo procesar la respuesta del análisis');
            }

            const result = JSON.parse(match[1]);
            if (userContext) {
                result.userContext = userContext;
            }

            hasResponded = true;
            res.json(result);
        } catch (error) {
            if (!hasResponded) {
                hasResponded = true;
                res.status(500).json({ 
                    error: 'Error al procesar el análisis',
                    details: errorOutput || error.message,
                    stdout: data
                });
            }
        }
    });

    pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        if (!hasResponded) {
            hasResponded = true;
            res.status(500).json({ 
                error: 'Error al ejecutar el analizador',
                details: error.message
            });
        }
    });
});

// Iniciar servidor
const port = process.env.PORT || 8080;
verifyPython()
    .then(() => {
        app.listen(port, '0.0.0.0', () => {
            console.log(`🚀 Servidor iniciado en puerto ${port}`);
            console.log(`🏥 Health check disponible en: http://0.0.0.0:${port}/health`);
        });
    })
    .catch(error => {
        console.error('❌ Error al iniciar:', error);
        process.exit(1);
    });