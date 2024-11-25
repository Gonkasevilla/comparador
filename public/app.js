document.addEventListener('DOMContentLoaded', () => {
    // Estado inicial de la aplicación
    const state = {
        products: [],
        history: JSON.parse(localStorage.getItem('searchHistory')) || [],
        currentTab: 'comparator'
    };

    // Referencias a elementos del DOM
    const elements = {
        tabs: document.querySelectorAll('.tab-button'),
        tabContents: document.querySelectorAll('.tab-content'),
        productForm: {
            input: document.getElementById('productUrl'),
            addButton: document.querySelector('.add-product-btn'),
            compareButton: document.querySelector('.compare-btn'),
            contextInput: document.getElementById('userContext'),
            productsList: document.querySelector('.products-list'),
            resultArea: document.querySelector('.comparison-result')
        },
        advisorForm: {
            form: document.getElementById('advisor-form'),
            resultArea: document.getElementById('advisor-result')
        },
        history: {
            list: document.querySelector('.history-list'),
            filters: document.querySelectorAll('.filter-btn'),
            clearButton: document.querySelector('.clear-history-btn')
        }
    };

    // Mensajes de carga aleatorios
    const loadingMessages = [
        "Analizando productos... 🔍",
        "Comparando características... 📊",
        "Consultando bases de datos... 📚",
        "Procesando información... ⚡",
        "Evaluando opciones... 🤔",
        "Preparando resultados... ✨",
        "Generando recomendaciones... 🎯"
    ];

    // Funciones de utilidad
    function getRandomLoadingMessage() {
        return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
    }

    function showLoading(container) {
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-message">${getRandomLoadingMessage()}</div>
            </div>
        `;
    }

    function showError(container, message) {
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error</h3>
                <p>${message}</p>
            </div>
        `;
    }

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 100);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    // Manejo de pestañas
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    function switchTab(tabId) {
        state.currentTab = tabId;
        
        // Actualizar pestañas
        elements.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
        });

        // Actualizar contenido
        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === tabId);
        });

        // Cargar contenido específico si es necesario
        if (tabId === 'history') {
            renderHistory();
        }
    }

    // Manejo del comparador
    elements.productForm.input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            elements.productForm.addButton.click();
        }
    });

    elements.productForm.addButton.addEventListener('click', () => {
        const url = elements.productForm.input.value.trim();
        if (validateUrl(url)) {
            addProduct(url);
            elements.productForm.input.value = '';
        } else {
            showNotification('Por favor, introduce una URL válida de una tienda compatible', 'error');
        }
    });

    elements.productForm.compareButton.addEventListener('click', async () => {
        const context = elements.productForm.contextInput.value.trim();
        showLoading(elements.productForm.resultArea);

        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    urls: state.products,
                    context: context
                })
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            renderComparison(data);
            saveToHistory('comparison', {
                products: state.products,
                context: context
            }, data);

        } catch (error) {
            showError(elements.productForm.resultArea, error.message);
            console.error('Error en la comparación:', error);
        }
    });

    function validateUrl(url) {
        try {
            new URL(url);
            return url.includes('http') && (
                url.includes('pccomponentes.com') ||
                url.includes('mediamarkt.es') ||
                url.includes('amazon.es') ||
                url.includes('carrefour.es') ||
                url.includes('elcorteingles.es') ||
                url.includes('fnac.es')
            );
        } catch {
            return false;
        }
    }
    // Manejo de productos
    function addProduct(url) {
        if (state.products.includes(url)) {
            showNotification('Este producto ya está en la lista', 'error');
            return;
        }

        state.products.push(url);
        renderProducts();
        updateCompareButton();
    }

    function deleteProduct(index) {
        state.products.splice(index, 1);
        renderProducts();
        updateCompareButton();
    }

    function renderProducts() {
        elements.productForm.productsList.innerHTML = state.products.map((url, index) => `
            <div class="product-card">
                <div class="product-info">
                    <p class="product-name">${getProductNameFromUrl(url)}</p>
                    <small class="product-url">${new URL(url).hostname}</small>
                </div>
                <button class="delete-product" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');

        // Añadir event listeners para eliminar productos
        document.querySelectorAll('.delete-product').forEach(button => {
            button.addEventListener('click', () => {
                const index = parseInt(button.dataset.index);
                deleteProduct(index);
            });
        });
    }

    function getProductNameFromUrl(url) {
        try {
            const pathname = new URL(url).pathname;
            return pathname
                .split('/')
                .pop()
                .replace(/-/g, ' ')
                .replace(/\.html$/, '')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        } catch {
            return 'Producto';
        }
    }

    function updateCompareButton() {
        const canCompare = state.products.length >= 2;
        elements.productForm.compareButton.disabled = !canCompare;
        elements.productForm.compareButton.classList.toggle('active', canCompare);
    }

    function renderComparison(data) {
        if (!data.analysis) {
            showError(elements.productForm.resultArea, 'No se pudo generar el análisis');
            return;
        }

        elements.productForm.resultArea.innerHTML = `
            <div class="comparison-content">
                ${data.analysis}
            </div>
        `;
    }
    function addProduct(url) {
        if (state.products.includes(url)) {
            showNotification('Este producto ya está en la lista', 'error');
            return;
        }

        state.products.push(url);
        renderProducts();
        updateCompareButton();
    }

    function renderProducts() {
        elements.productForm.productsList.innerHTML = state.products.map((url, index) => `
            <div class="product-card">
                <div class="product-info">
                    <p class="product-name">${getProductNameFromUrl(url)}</p>
                    <small class="product-url">${new URL(url).hostname}</small>
                </div>
                <button class="delete-product" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');

        // Agregar listeners para eliminar productos
        document.querySelectorAll('.delete-product').forEach(button => {
            button.addEventListener('click', () => {
                const index = parseInt(button.dataset.index);
                deleteProduct(index);
            });
        });
    }

    function getProductNameFromUrl(url) {
        try {
            const pathname = new URL(url).pathname;
            return pathname
                .split('/')
                .pop()
                .replace(/-/g, ' ')
                .replace('.html', '')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        } catch {
            return 'Producto';
        }
    }

    function deleteProduct(index) {
        state.products.splice(index, 1);
        renderProducts();
        updateCompareButton();
    }

    function updateCompareButton() {
        const canCompare = state.products.length >= 2;
        elements.productForm.compareButton.disabled = !canCompare;
        elements.productForm.compareButton.classList.toggle('active', canCompare);
    }

    // Manejo del recomendador
    elements.advisorForm.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            productType: document.getElementById('product-type').value,
            minBudget: document.getElementById('min-budget').value,
            maxBudget: document.getElementById('max-budget').value,
            mainUse: document.getElementById('main-use').value,
            specificNeeds: document.getElementById('specific-needs').value
        };

        showLoading(elements.advisorForm.resultArea);

        try {
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            renderRecommendation(data);
            saveToHistory('recommendation', formData, data);

        } catch (error) {
            showError(elements.advisorForm.resultArea, error.message);
        }
    });
    // Manejo del historial
    function saveToHistory(type, request, response) {
        const historyItem = {
            id: Date.now(),
            type: type,
            date: new Date().toISOString(),
            request: request,
            response: response
        };

        state.history.unshift(historyItem);
        if (state.history.length > 10) {
            state.history.pop();
        }

        localStorage.setItem('searchHistory', JSON.stringify(state.history));
        if (state.currentTab === 'history') {
            renderHistory();
        }
    }

    function renderHistory(filter = 'all') {
        const filteredHistory = state.history.filter(item => 
            filter === 'all' || item.type === filter
        );

        if (filteredHistory.length === 0) {
            elements.history.list.innerHTML = `
                <div class="empty-history">
                    <i class="fas fa-history"></i>
                    <p>No hay elementos en el historial</p>
                </div>
            `;
            return;
        }

        elements.history.list.innerHTML = filteredHistory.map(item => 
            createHistoryItemHTML(item)
        ).join('');

        // Agregar event listeners para las acciones del historial
        addHistoryEventListeners();
    }

    function createHistoryItemHTML(item) {
        const date = new Date(item.date).toLocaleString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const typeIcon = item.type === 'comparison' ? 'exchange-alt' : 'magic';
        const typeText = item.type === 'comparison' ? 'Comparación' : 'Recomendación';

        const summaryText = item.type === 'comparison'
            ? `Comparación de ${item.request.urls?.length || 0} productos`
            : `Búsqueda de ${item.request.productType} (${item.request.minBudget}€ - ${item.request.maxBudget}€)`;

        return `
            <div class="history-item" data-id="${item.id}">
                <div class="history-item-header">
                    <span class="history-date">
                        <i class="fas fa-calendar"></i> ${date}
                    </span>
                    <span class="history-type">
                        <i class="fas fa-${typeIcon}"></i> ${typeText}
                    </span>
                </div>
                <div class="history-content">
                    <p>${summaryText}</p>
                </div>
                <div class="history-actions">
                    <button class="view-details-btn">
                        <i class="fas fa-eye"></i> Ver detalles
                    </button>
                    <button class="delete-item-btn">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    function addHistoryEventListeners() {
        // Filtros del historial
        elements.history.filters.forEach(filter => {
            filter.addEventListener('click', () => {
                elements.history.filters.forEach(f => f.classList.remove('active'));
                filter.classList.add('active');
                renderHistory(filter.dataset.filter);
            });
        });

        // Limpiar historial
        elements.history.clearButton.addEventListener('click', () => {
            if (confirm('¿Estás seguro de que quieres borrar todo el historial?')) {
                state.history = [];
                localStorage.removeItem('searchHistory');
                renderHistory();
            }
        });

        // Ver detalles y eliminar items
        document.querySelectorAll('.view-details-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const historyItem = e.target.closest('.history-item');
                const itemId = parseInt(historyItem.dataset.id);
                const item = state.history.find(h => h.id === itemId);
                if (item) {
                    showHistoryItemDetails(item);
                }
            });
        });

        document.querySelectorAll('.delete-item-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const historyItem = e.target.closest('.history-item');
                const itemId = parseInt(historyItem.dataset.id);
                deleteHistoryItem(itemId);
            });
        });
    }

    function showHistoryItemDetails(item) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${item.type === 'comparison' ? 'Comparación' : 'Recomendación'}</h3>
                    <button class="close-modal"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    ${item.response.analysis || ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('show'), 10);

        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        });
    }

    function deleteHistoryItem(itemId) {
        const index = state.history.findIndex(item => item.id === itemId);
        if (index !== -1) {
            state.history.splice(index, 1);
            localStorage.setItem('searchHistory', JSON.stringify(state.history));
            renderHistory();
        }
    }

    // Inicialización
    renderHistory();
});