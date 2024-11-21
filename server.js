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
app.use(express.json({limit: '1mb'}));
app.use(express.static(path.join(__dirname, 'public')));

// Health check endpoint
app.get('/health', (_, res) => res.send('OK'));

// Ruta raíz
app.get('/', (_, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Validación de URLs
const isValidUrl = (url) => {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
};

// API route con validación mejorada
app.post('/api/compare', (req, res) => {
    const { urls, userContext } = req.body;

    // Validación de URLs
    if (!urls || !Array.isArray(urls)) {
        return res.status(400).json({ error: 'Se requiere un array de URLs' });
    }

    if (urls.length < 2) {
        return res.status(400).json({ error: 'Se requieren al menos dos URLs para comparar' });
    }

    if (urls.length > 5) {
        return res.status(400).json({ error: 'Máximo 5 productos para comparar' });
    }

    if (!urls.every(isValidUrl)) {
        return res.status(400).json({ error: 'Una o más URLs no son válidas' });
    }

    // Validación del contexto
    if (userContext && typeof userContext !== 'string') {
        return res.status(400).json({ error: 'El contexto debe ser texto' });
    }

    if (userContext && userContext.length > 500) {
        return res.status(400).json({ error: 'El contexto es demasiado largo (máximo 500 caracteres)' });
    }

    console.log('📊 Analizando productos con contexto:', userContext || 'Sin contexto');

    // Crear argumentos para Python
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
    let timeout;

    // Establecer timeout de 30 segundos
    timeout = setTimeout(() => {
        pythonProcess.kill();
        res.status(504).json({ 
            error: 'El análisis ha tardado demasiado tiempo',
            details: 'Timeout de 30 segundos excedido'
        });
    }, 30000);

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

    pythonProcess.on('close', code => {
        clearTimeout(timeout);
        console.log('📋 Código de salida Python:', code);
        try {
            const match = data.match(/RESULT_JSON_START\n([\s\S]*?)\nRESULT_JSON_END/);
            if (!match) {
                throw new Error('No se pudo procesar la respuesta del análisis');
            }

            const result = JSON.parse(match[1]);
            if (userContext) {
                result.userContext = userContext;
            }

            res.json(result);
        } catch (error) {
            console.error('❌ Error procesando resultado:', error);
            res.status(500).json({ 
                error: 'Error al procesar el análisis',
                details: errorOutput || error.message,
                stdout: data
            });
        }
    });

    pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        console.error('❌ Error al ejecutar Python:', error);
        res.status(500).json({ 
            error: 'Error al ejecutar el analizador',
            details: error.message
        });
    });
});

// Iniciar servidor
const port = process.env.PORT || 3000;
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