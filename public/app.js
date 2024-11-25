document.addEventListener('DOMContentLoaded', () => {
    const state = {
        products: [],
        history: (() => {
            try {
                return JSON.parse(localStorage.getItem('searchHistory')) || [];
            } catch {
                return [];
            }
        })(),
        currentTab: 'comparator'
    };
 
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
 
    const loadingMessages = [
        "Analizando productos... 🔍",
        "Comparando características... 📊",
        "Procesando información... ⚡",
        "Evaluando opciones... 🤔",
        "Preparando resultados... ✨",
        "Generando recomendaciones... 🎯"
    ];
 
    function getRandomLoadingMessage() {
        return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
    }
 
    function showLoading(container) {
        if (!container) return;
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-message">${getRandomLoadingMessage()}</div>
            </div>
        `;
    }
 
    function showError(container, message) {
        if (!container) return;
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
 
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            if (tabId) switchTab(tabId);
        });
    });
 
    function switchTab(tabId) {
        if (!tabId) return;
        state.currentTab = tabId;
        
        elements.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
        });
 
        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === tabId);
        });
 
        if (tabId === 'history') {
            renderHistory();
        }
    }
 
    elements.productForm.input?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            elements.productForm.addButton?.click();
        }
    });
 
    elements.productForm.addButton?.addEventListener('click', () => {
        const url = elements.productForm.input?.value.trim();
        if (url && validateUrl(url)) {
            addProduct(url);
            elements.productForm.input.value = '';
        } else {
            showNotification('Por favor, introduce una URL válida de una tienda compatible', 'error');
        }
    });
 
    elements.productForm.compareButton?.addEventListener('click', async () => {
        const context = elements.productForm.contextInput?.value.trim() || '';
        showLoading(elements.productForm.resultArea);
 
        try {
            const requestData = {
                urls: state.products,
                context: context
            };
 
            console.log('Enviando datos:', requestData);
 
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
 
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
 
            const data = await response.json();
            console.log('Respuesta recibida:', data);
 
            if (data.error) {
                throw new Error(data.error);
            }
 
            renderComparison(data);
            saveToHistory('comparison', {
                products: state.products.slice(),
                context: context
            }, data);
 
        } catch (error) {
            console.error('Error en comparación:', error);
            showError(elements.productForm.resultArea, error.message);
        }
    });
 
    function validateUrl(url) {
        try {
            new URL(url);
            const validDomains = [
                'pccomponentes.com',
                'mediamarkt.es',
                'amazon.es',
                'carrefour.es',
                'elcorteingles.es',
                'fnac.es'
            ];
            return validDomains.some(domain => url.toLowerCase().includes(domain));
        } catch {
            return false;
        }
    }
 
    function addProduct(url) {
        if (!url || state.products.includes(url)) {
            showNotification('Este producto ya está en la lista', 'error');
            return;
        }
 
        state.products.push(url);
        renderProducts();
        updateCompareButton();
    }
 
    function deleteProduct(index) {
        if (index >= 0 && index < state.products.length) {
            state.products.splice(index, 1);
            renderProducts();
            updateCompareButton();
        }
    }
 
    function renderProducts() {
        if (!elements.productForm.productsList) return;
 
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
 
        document.querySelectorAll('.delete-product').forEach(button => {
            button.addEventListener('click', () => {
                const index = parseInt(button.dataset.index);
                if (!isNaN(index)) {
                    deleteProduct(index);
                }
            });
        });
    }
 
    function getProductNameFromUrl(url) {
        try {
            const pathname = new URL(url).pathname;
            return pathname
                .split('/')
                .filter(part => part)
                .pop()
                .replace(/-/g, ' ')
                .replace(/\.html$/, '')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ') || 'Producto';
        } catch {
            return 'Producto';
        }
    }
 
    function updateCompareButton() {
        if (!elements.productForm.compareButton) return;
        const canCompare = state.products.length >= 2;
        elements.productForm.compareButton.disabled = !canCompare;
        elements.productForm.compareButton.classList.toggle('active', canCompare);
    }
 
    function renderComparison(data) {
        if (!elements.productForm.resultArea) return;
        if (!data?.analysis) {
            showError(elements.productForm.resultArea, 'No se pudo generar el análisis');
            return;
        }
 
        elements.productForm.resultArea.innerHTML = `
            <div class="comparison-content">
                ${data.analysis}
            </div>
        `;
    }
 
    elements.advisorForm.form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            productType: document.getElementById('product-type')?.value || '',
            minBudget: document.getElementById('min-budget')?.value || '',
            maxBudget: document.getElementById('max-budget')?.value || '',
            mainUse: document.getElementById('main-use')?.value || '',
            specificNeeds: document.getElementById('specific-needs')?.value || ''
        };
 
        if (!formData.productType || !formData.minBudget || !formData.maxBudget) {
            showNotification('Por favor, completa los campos requeridos', 'error');
            return;
        }
 
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
            console.log('Respuesta del recomendador:', data);
 
            if (data.error) {
                throw new Error(data.error);
            }
 
            renderRecommendation(data);
            saveToHistory('recommendation', formData, data);
 
        } catch (error) {
            console.error('Error en recomendación:', error);
            showError(elements.advisorForm.resultArea, error.message);
        }
    });
 
    function renderRecommendation(data) {
        if (!elements.advisorForm.resultArea) return;
        if (!data?.analysis) {
            showError(elements.advisorForm.resultArea, 'No se pudo generar la recomendación');
            return;
        }
 
        elements.advisorForm.resultArea.innerHTML = `
            <div class="advisor-result">
                <div class="recommendation-content">
                    ${data.analysis}
                </div>
            </div>
        `;
    }
 
    function saveToHistory(type, request, response) {
        try {
            const historyItem = {
                id: Date.now(),
                type,
                date: new Date().toISOString(),
                request: type === 'comparison' 
                    ? { products: request.products, context: request.context }
                    : request,
                response: {
                    analysis: response.analysis
                }
            };
 
            state.history.unshift(historyItem);
            if (state.history.length > 10) {
                state.history.pop();
            }
 
            localStorage.setItem('searchHistory', JSON.stringify(state.history));
            if (state.currentTab === 'history') {
                renderHistory();
            }
        } catch (error) {
            console.error('Error guardando historial:', error);
        }
    }
 
    function renderHistory(filter = 'all') {
        if (!elements.history.list) return;
 
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
 
        elements.history.list.innerHTML = filteredHistory
            .map(item => createHistoryItemHTML(item))
            .join('');
 
        addHistoryEventListeners();
    }
 
    function createHistoryItemHTML(item) {
        if (!item?.request) return '';
 
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
            ? `Comparación de ${Array.isArray(item.request.products) ? item.request.products.length : 0} productos`
            : `Búsqueda de ${item.request.productType || 'producto'} (${item.request.minBudget || 0}€ - ${item.request.maxBudget || 0}€)`;
 
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
        elements.history.filters?.forEach(filter => {
            filter.addEventListener('click', () => {
                elements.history.filters.forEach(f => f.classList.remove('active'));
                filter.classList.add('active');
                renderHistory(filter.dataset.filter);
            });
        });
 
        elements.history.clearButton?.addEventListener('click', () => {
            if (confirm('¿Estás seguro de que quieres borrar todo el historial?')) {
                state.history = [];
                localStorage.removeItem('searchHistory');
                renderHistory();
            }
        });
 
        document.querySelectorAll('.view-details-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const historyItem = e.target.closest('.history-item');
                if (!historyItem) return;
                
                const itemId = parseInt(historyItem.dataset.id);
                if (isNaN(itemId)) return;
 
                const item = state.history.find(h => h.id === itemId);
                if (item) {
                    showHistoryItemDetails(item);
                }
            });
        });
 
        document.querySelectorAll('.delete-item-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const historyItem = e.target.closest('.history-item');
                if (!historyItem) return;
                
                const itemId = parseInt(historyItem.dataset.id);
                if (isNaN(itemId)) return;
                
                deleteHistoryItem(itemId);
            });
        });
    }
 
    function showHistoryItemDetails(item) {
        if (!item?.response) return;
 
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${item.type === 'comparison' ? 'Comparación' : 'Recomendación'}</h3>
                   <button class="close-modal"><i class="fas fa-times"></i></button>
               </div>
               <div class="modal-body">
                   ${item.response.analysis || 'No hay detalles disponibles'}
               </div>
           </div>
       `;

       document.body.appendChild(modal);
       setTimeout(() => modal.classList.add('show'), 10);

       modal.querySelector('.close-modal')?.addEventListener('click', () => {
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

   renderHistory();
});
                        