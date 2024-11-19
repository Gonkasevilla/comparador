document.addEventListener('DOMContentLoaded', () => {
    const comparisonForm = document.querySelector('.comparison-form');
    const productUrlInput = document.getElementById('productUrl');
    const addProductBtn = document.querySelector('.add-product-btn');
    const productsList = document.querySelector('.products-list');
    const compareBtn = document.querySelector('.compare-btn');
    const comparisonResult = document.querySelector('.comparison-result');
    const products = [];

    const updateCompareButton = () => {
        const isActive = products.length >= 2;
        compareBtn.classList.toggle('active', isActive);
        compareBtn.disabled = !isActive;
        compareBtn.innerHTML = isActive ? 
            '<i class="fas fa-magic"></i> Comparar Productos' : 
            '<i class="fas fa-info-circle"></i> Añade al menos 2 productos';
    };

    const createProductCard = (url, index) => {
        const card = document.createElement('div');
        card.className = 'product-card';
        
        // Extraer nombre del producto de la URL
        const urlObj = new URL(url);
        const productName = urlObj.pathname.split('/').pop()
            .replace(/-/g, ' ')
            .replace(/\.html$/, '')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');

        card.innerHTML = `
            <div class="product-info">
                <div class="product-name">${productName}</div>
                <div class="product-site">
                    <i class="fas fa-link"></i>
                    ${urlObj.hostname.replace('www.', '')}
                </div>
            </div>
            <button class="delete-product" data-index="${index}" title="Eliminar producto">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Añadir animación de entrada
        card.style.animation = 'slideIn 0.3s ease-out forwards';
        
        return card;
    };

    const updateProductsList = () => {
        productsList.innerHTML = '';
        products.forEach((url, index) => {
            productsList.appendChild(createProductCard(url, index));
        });
        updateCompareButton();
    };

    const formatAnalysis = (analysis) => {
        // Primero limpiamos el texto de asteriscos y convertimos a negrita HTML
        let formattedText = analysis.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convertimos todos los guiones en puntos para las viñetas
        formattedText = formattedText.replace(/^- /gm, '• ');
    
        const sections = formattedText.split('###').filter(section => section.trim());
        
        return `
            <div class="analysis-container">
                ${sections.map(section => {
                    const [title, ...content] = section.split('\n').filter(line => line.trim());
                    
                    return `
                        <div class="analysis-section ${title.toLowerCase().includes('resumen') ? 'highlight-section' : ''}">
                            <h3 class="section-title ${title.includes('🎯') ? 'with-emoji' : ''}">
                                ${title.trim()}
                            </h3>
                            <div class="section-content">
                                ${content.map(line => {
                                    if (line.trim().startsWith('•')) {
                                        return `<div class="bullet-point">${line.trim()}</div>`;
                                    } else if (line.trim().startsWith('✓')) {
                                        return `<div class="advantage">${line.trim()}</div>`;
                                    } else if (line.trim().startsWith('✗')) {
                                        return `<div class="disadvantage">${line.trim()}</div>`;
                                    } else {
                                        return `<p>${line.trim()}</p>`;
                                    }
                                }).join('')}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    };

    const loadingMessages = [
        "🏃‍♂️ Visitando las tiendas por ti para probar el producto...",
        "📦 Haciendo unboxing para que no tengas que hacerlo...",
        "👴 Consultando con mi abuelo si le vale o no...",
        "🤔 Comparando precios como si fuera mi propio dinero...",
        "🔍 Leyendo la letra pequeña que nadie lee...",
        "📱 Probando si resiste una caída (mejor yo que tú)...",
        "🛒 Peleando en el Black Friday virtual por ti...",
        "📊 Analizando más datos que mi ex en Instagram...",
        "🤓 Leyendo todos los manuales (alguien tiene que hacerlo)...",
        "🎮 Probando si sirve para gaming (por motivos científicos)..."
    ];
    
    const getRandomLoadingMessage = () => {
        return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
    };
    
    // Modificar la parte del loading en el evento click del compareBtn
    compareBtn.addEventListener('click', async () => {
        if (products.length < 2) return;
    
        comparisonResult.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <div class="loading-message">${getRandomLoadingMessage()}</div>
                <div class="loading-submessage">Esto puede tomar unos segundos...</div>
            </div>
        `;
    
        // Cambiar el mensaje cada 3 segundos mientras carga
        const messageInterval = setInterval(() => {
            const loadingMessage = document.querySelector('.loading-message');
            if (loadingMessage) {
                loadingMessage.innerHTML = getRandomLoadingMessage();
            }
        }, 3000);
    
        try {
            // ... resto del código de la comparación ...
        } finally {
            clearInterval(messageInterval);
        }
    });

    addProductBtn.addEventListener('click', () => {
        const url = productUrlInput.value.trim();
        
        if (!url) {
            showNotification('Por favor, introduce la URL del producto', 'error');
            return;
        }

        try {
            new URL(url);
            products.push(url);
            productUrlInput.value = '';
            updateProductsList();
            showNotification('Producto añadido correctamente', 'success');
        } catch (e) {
            showNotification('Por favor, introduce una URL válida', 'error');
        }
    });

    productUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addProductBtn.click();
        }
    });

    productsList.addEventListener('click', (e) => {
        if (e.target.closest('.delete-product')) {
            const card = e.target.closest('.product-card');
            card.style.animation = 'slideOut 0.3s ease-out forwards';
            
            card.addEventListener('animationend', () => {
                const index = e.target.closest('.delete-product').dataset.index;
                products.splice(index, 1);
                updateProductsList();
            });
        }
    });

    compareBtn.addEventListener('click', async () => {
        if (products.length < 2) return;

        comparisonResult.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <div class="loading-text">
                    <h3>Analizando productos</h3>
                    <p>Nuestro experto está comparando los productos...</p>
                </div>
            </div>
        `;

        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls: products })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            comparisonResult.innerHTML = formatAnalysis(data.analysis);
            
            // Scroll suave hasta el resultado
            comparisonResult.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            comparisonResult.innerHTML = `
                <div class="error-container">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Ha ocurrido un error</h3>
                    <p>${error.message || 'Error al comparar los productos'}</p>
                    <button class="retry-button" onclick="location.reload()">
                        <i class="fas fa-redo"></i> Intentar de nuevo
                    </button>
                </div>
            `;
        }
    });

    const showNotification = (message, type = 'info') => {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i>
            ${message}
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }, 100);
    };

    updateCompareButton();
});