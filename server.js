const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Health check más simple posible
app.get('/health', (_, res) => res.send('OK'));

// Ruta raíz
app.get('/', (_, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API route
app.post('/api/compare', (req, res) => {
    const { urls } = req.body;
    if (!urls || !Array.isArray(urls)) {
        return res.status(400).json({ error: 'URLs inválidas' });
    }

    const pythonProcess = spawn('python3', [
        path.join(__dirname, 'backend', 'scrapers', 'perplexity_analyzer.py'),
        ...urls
    ]);

    let data = '';

    pythonProcess.stdout.on('data', chunk => data += chunk);
    pythonProcess.stderr.on('data', error => console.error(error.toString()));
    pythonProcess.on('close', code => {
        try {
            const match = data.match(/RESULT_JSON_START\n([\s\S]*?)\nRESULT_JSON_END/);
            res.json(match ? JSON.parse(match[1]) : { error: 'Error en análisis' });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
});

// Iniciar servidor
const port = process.env.PORT || 3000;
app.listen(port, '0.0.0.0', () => {
    console.log(`Servidor iniciado en puerto ${port}`);
});