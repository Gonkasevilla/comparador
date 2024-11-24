document.addEventListener('DOMContentLoaded', () => {
    // Estado inicial de la aplicación
    const state = {
        products: [],
        currentTab: 'comparator',
        history: JSON.parse(localStorage.getItem('searchHistory')) || []
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

    // Navegación por pestañas
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    function switchTab(tabId) {
        // Actualizar estado
        state.currentTab = tabId;

        // Actualizar clases activas
        elements.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
        });

        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === tabId);
        });

        // Cargar contenido específico de la pestaña si es necesario
        if (tabId === 'history') {
            renderHistory();
        }
    }

    // Mensajes de carga aleatorios
    const loadingMessages = [
        "Analizando productos con IA... 🤖",
        "Comparando características... 📊",
        "Evaluando precios... 💰",
        "Buscando las mejores opciones... 🔍",
        "Consultando bases de datos... 📚",
        "Procesando información... ⚡",
        "Preparando recomendaciones... 🎯"
    ];

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
    // Manejo de productos
    elements.productForm.addButton.addEventListener('click', () => {
        const url = elements.productForm.input.value.trim();
        if (validateUrl(url)) {
            addProduct(url);
            elements.productForm.input.value = '';
        } else {
            showNotification('Por favor, introduce una URL válida', 'error');
        }
    });

    elements.productForm.input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            elements.productForm.addButton.click();
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

        // Agregar event listeners para eliminar productos
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

        elements.history.list.innerHTML = filteredHistory.length ? 
            filteredHistory.map(item => createHistoryItemHTML(item)).join('') :
            `<div class="empty-history">No hay elementos en el historial</div>`;

        // Agregar event listeners para las acciones del historial
        addHistoryEventListeners();
    }

    function createHistoryItemHTML(item) {
        const date = new Date(item.date).toLocaleString();
        const typeIcon = item.type === 'comparison' ? 'exchange-alt' : 'magic';
        const typeText = item.type === 'comparison' ? 'Comparación' : 'Recomendación';

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
                    ${getHistoryItemSummary(item)}
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

    function getHistoryItemSummary(item) {
        if (item.type === 'comparison') {
            return `Comparación de ${item.request.products.length} productos`;
        } else {
            return `Búsqueda de ${item.request.productType} - Presupuesto: ${item.request.minBudget}€ - ${item.request.maxBudget}€`;
        }
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

        // Botón de limpiar historial
        elements.history.clearButton.addEventListener('click', () => {
            if (confirm('¿Estás seguro de que quieres borrar todo el historial?')) {
                state.history = [];
                localStorage.removeItem('searchHistory');
                renderHistory();
            }
        });

        // Botones de acciones en elementos del historial
        document.querySelectorAll('.view-details-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const historyItem = e.target.closest('.history-item');
                const itemId = parseInt(historyItem.dataset.id);
                showHistoryItemDetails(itemId);
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

    // Funciones de utilidad
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
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

    // Inicialización
    renderHistory();
});
