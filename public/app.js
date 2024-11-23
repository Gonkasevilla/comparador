document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const productUrlInput = document.getElementById('productUrl');
    const userContextInput = document.getElementById('userContext');
    const addProductBtn = document.querySelector('.add-product-btn');
    const productsList = document.querySelector('.products-list');
    const compareBtn = document.querySelector('.compare-btn');
    const comparisonResult = document.querySelector('.comparison-result');
    const advisorForm = document.querySelector('.advisor-form');
    const advisorResult = document.querySelector('.advisor-result');
    const historyFilters = document.querySelectorAll('.filter-btn');
    const clearHistoryBtn = document.querySelector('.clear-history-btn');
    const historyList = document.querySelector('.history-list');

    const products = [];
    
    // Loading Messages
    const loadingMessages = {
        comparison: [
            "🛍️ Visitando las tiendas por ti...",
            "📦 Haciendo unboxing para que tú no tengas que hacerlo...",
            "🤔 Consultando con expertos...",
            "🔍 Analizando cada detalle...",
            "📊 Comparando características...",
            "💡 Pensando en tus necesidades..."
        ],
        advisor: [
            "🔍 Buscando los mejores productos para ti...",
            "📊 Analizando tus necesidades...",
            "💡 Encontrando las mejores opciones...",
            "🎯 Ajustando recomendaciones a tu presupuesto...",
            "⭐ Seleccionando productos de calidad...",
            "📱 Verificando disponibilidad..."
        ]
    };

    // History Management
    const saveToHistory = (type, data) => {
        const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        const newEntry = {
            id: Date.now(),
            type,
            date: new Date().toISOString(),
            data
        };
        history.unshift(newEntry);
        localStorage.setItem('searchHistory', JSON.stringify(history.slice(0, 10)));
        updateHistoryView();
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getRandomLoadingMessage = (type) => {
        const messages = loadingMessages[type];
        return messages[Math.floor(Math.random() * messages.length)];
    };

    // UI Updates
    const updateCompareButton = () => {
        const isActive = products.length >= 2;
        compareBtn.classList.toggle('active', isActive);
        compareBtn.disabled = !isActive;
    };
    // Product Card Creation
    const createProductCard = (url, index) => {
        const card = document.createElement('div');
        card.className = 'product-card animate__animated animate__fadeIn';
        
        const urlObj = new URL(url);
        const productName = urlObj.pathname
            .split('/')
            .pop()
            .replace(/-/g, ' ')
            .replace(/\.html$/, '')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');

        card.innerHTML = `
            <div class="product-info">
                <p class="product-name">${productName}</p>
                <small class="product-url">${urlObj.hostname}</small>
            </div>
            <button class="delete-product" data-index="${index}">
                <i class="fas fa-times"></i>
            </button>
        `;
        return card;
    };

    const updateProductsList = () => {
        productsList.innerHTML = '';
        products.forEach((url, index) => {
            productsList.appendChild(createProductCard(url, index));
        });
        updateCompareButton();
    };

    const showLoadingMessage = (element, type) => {
        element.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p class="loading-message">${getRandomLoadingMessage(type)}</p>
            </div>
        `;
    };

    const updateHistoryView = (filter = 'all') => {
        const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        const filteredHistory = filter === 'all' ? 
            history : 
            history.filter(item => item.type === filter);

        if (filteredHistory.length === 0) {
            historyList.innerHTML = `
                <div class="empty-history">
                    <i class="fas fa-history fa-3x"></i>
                    <p>No hay búsquedas en el historial</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = filteredHistory.map(item => `
            <div class="history-item" data-id="${item.id}">
                <div class="history-item-header">
                    <div class="history-item-type">
                        <i class="fas fa-${item.type === 'comparison' ? 'balance-scale' : 'magic'}"></i>
                        ${item.type === 'comparison' ? 'Comparación' : 'Recomendación'}
                    </div>
                    <span class="history-item-date">${formatDate(item.date)}</span>
                </div>
                <div class="history-item-content">
                    ${formatHistoryContent(item)}
                </div>
            </div>
        `).join('');
    };

    const formatHistoryContent = (item) => {
        if (item.type === 'comparison') {
            return `
                <div class="compared-products">
                    <strong>Productos comparados:</strong>
                    <ul>
                        ${item.data.products.map(p => `<li>${p}</li>`).join('')}
                    </ul>
                </div>
            `;
        } else {
            return `
                <div class="recommendation-summary">
                    <strong>Búsqueda:</strong>
                    <p>${item.data.userNeeds}</p>
                    <strong>Presupuesto:</strong>
                    <p>Hasta ${item.data.maxBudget}€</p>
                </div>
            `;
        }
    };
    // Event Listeners
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            const tabId = button.dataset.tab;
            document.getElementById(tabId).classList.add('active');
        });
    });

    addProductBtn.addEventListener('click', () => {
        const url = productUrlInput.value.trim();
        if (!url) {
            alert('Por favor, introduce una URL de producto');
            return;
        }
        try {
            new URL(url);
            products.push(url);
            productUrlInput.value = '';
            updateProductsList();
        } catch (e) {
            alert('Por favor, introduce una URL válida');
        }
    });

    productUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addProductBtn.click();
        }
    });

    productsList.addEventListener('click', (e) => {
        if (e.target.closest('.delete-product')) {
            const index = e.target.closest('.delete-product').dataset.index;
            products.splice(index, 1);
            updateProductsList();
        }
    });

    compareBtn.addEventListener('click', async () => {
        if (products.length < 2) return;
        
        showLoadingMessage(comparisonResult, 'comparison');
        let currentMessageIndex = 0;
        
        const messageInterval = setInterval(() => {
            const loadingMessage = document.querySelector('.loading-message');
            if (loadingMessage) {
                currentMessageIndex = (currentMessageIndex + 1) % loadingMessages.comparison.length;
                loadingMessage.textContent = loadingMessages.comparison[currentMessageIndex];
            }
        }, 3000);

        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    urls: products,
                    userContext: userContextInput.value.trim()
                })
            });
            
            clearInterval(messageInterval);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const formattedAnalysis = data.analysis
                .replace(/### (.*?)$/gm, (match, title) => {
                    const titleWithEmoji = title.includes('💡') ? title : title;
                    return `<h3>${titleWithEmoji}</h3>`;
                })
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/•\s/g, '')
                .split('\n').filter(line => line.trim()).join('\n');

            comparisonResult.innerHTML = `
                <div class="comparison-content animate__animated animate__fadeIn">
                    ${formattedAnalysis}
                </div>
            `;

            // Save to history
            saveToHistory('comparison', {
                products: products.map(url => {
                    const urlObj = new URL(url);
                    return urlObj.pathname.split('/').pop().replace(/-/g, ' ');
                }),
                result: data.analysis
            });

            comparisonResult.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start'
            });

        } catch (error) {
            clearInterval(messageInterval);
            comparisonResult.innerHTML = `
                <div class="error animate__animated animate__fadeIn">
                    <h3>Ha ocurrido un error</h3>
                    <p>${error.message || 'Error al realizar la comparación'}</p>
                </div>
            `;
        }
    });
    // Advisor Form Handler
    advisorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const productType = document.getElementById('productType').value;
        const minBudget = document.getElementById('minBudget').value;
        const maxBudget = document.getElementById('maxBudget').value;
        const mainUse = document.getElementById('mainUse').value;
        const userNeeds = document.getElementById('userNeeds').value;

        if (!productType || !maxBudget || !mainUse || !userNeeds) {
            alert('Por favor, completa todos los campos requeridos');
            return;
        }

        showLoadingMessage(advisorResult, 'advisor');
        let currentMessageIndex = 0;
        
        const messageInterval = setInterval(() => {
            const loadingMessage = document.querySelector('.loading-message');
            if (loadingMessage) {
                currentMessageIndex = (currentMessageIndex + 1) % loadingMessages.advisor.length;
                loadingMessage.textContent = loadingMessages.advisor[currentMessageIndex];
            }
        }, 3000);

        try {
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    productType,
                    minBudget,
                    maxBudget,
                    mainUse,
                    userNeeds
                })
            });

            clearInterval(messageInterval);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Format recommendations similarly to comparisons
            const formattedRecommendations = data.recommendations
                .replace(/### (.*?)$/gm, (match, title) => `<h3>${title}</h3>`)
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/•\s/g, '')
                .split('\n')
                .filter(line => line.trim())
                .join('\n');

            advisorResult.innerHTML = `
                <div class="recommendations-content animate__animated animate__fadeIn">
                    ${formattedRecommendations}
                </div>
            `;

            // Save to history
            saveToHistory('recommendation', {
                productType,
                maxBudget,
                mainUse,
                userNeeds,
                result: data.recommendations
            });

            advisorResult.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });

        } catch (error) {
            clearInterval(messageInterval);
            advisorResult.innerHTML = `
                <div class="error animate__animated animate__fadeIn">
                    <h3>Ha ocurrido un error</h3>
                    <p>${error.message || 'Error al obtener recomendaciones'}</p>
                </div>
            `;
        }
    });

    // History Event Listeners
    historyFilters.forEach(btn => {
        btn.addEventListener('click', () => {
            historyFilters.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateHistoryView(btn.dataset.filter);
        });
    });

    clearHistoryBtn.addEventListener('click', () => {
        if (confirm('¿Estás seguro de que quieres borrar todo el historial?')) {
            localStorage.removeItem('searchHistory');
            updateHistoryView();
        }
    });

    // History Item Click Handler
    historyList.addEventListener('click', (e) => {
        const historyItem = e.target.closest('.history-item');
        if (historyItem) {
            const id = historyItem.dataset.id;
            const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
            const item = history.find(h => h.id.toString() === id);
            
            if (item) {
                // Switch to appropriate tab
                const tabButton = document.querySelector(`.tab-button[data-tab="${item.type === 'comparison' ? 'comparator' : 'advisor'}"]`);
                tabButton.click();
                
                // Show the result
                const resultContainer = item.type === 'comparison' ? comparisonResult : advisorResult;
                resultContainer.innerHTML = `
                    <div class="${item.type === 'comparison' ? 'comparison' : 'recommendations'}-content animate__animated animate__fadeIn">
                        ${item.data.result}
                    </div>
                `;
                
                resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    });

    // Initial Setup
    updateCompareButton();
    updateHistoryView();
});