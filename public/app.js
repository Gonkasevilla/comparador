document.addEventListener('DOMContentLoaded', () => {
    const comparisonForm = document.querySelector('.comparison-form');
    const productUrlInput = document.getElementById('productUrl');
    const userContextInput = document.getElementById('userContext');
    const addProductBtn = document.querySelector('.add-product-btn');
    const productsList = document.querySelector('.products-list');
    const compareBtn = document.querySelector('.compare-btn');
    const comparisonResult = document.querySelector('.comparison-result');

    const products = [];
    
    const loadingMessages = [
        "🛍️ Visitando las tiendas por ti...",
        "📦 Haciendo unboxing para que tú no tengas que hacerlo...",
        "🤔 Consultando con expertos...",
        "🔍 Analizando cada detalle...",
        "📊 Comparando características...",
        "💡 Pensando en tus necesidades..."
    ];

    const updateCompareButton = () => {
        const isActive = products.length >= 2;
        compareBtn.classList.toggle('active', isActive);
        compareBtn.disabled = !isActive;
    };

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

    const getRandomLoadingMessage = () => {
        const randomIndex = Math.floor(Math.random() * loadingMessages.length);
        return loadingMessages[randomIndex];
    };

    const showLoadingMessage = () => {
        comparisonResult.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p class="loading-message">${getRandomLoadingMessage()}</p>
            </div>
        `;
    };

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
        
        showLoadingMessage();
        let currentMessageIndex = 0;
        
        const messageInterval = setInterval(() => {
            const loadingMessage = document.querySelector('.loading-message');
            if (loadingMessage) {
                currentMessageIndex = (currentMessageIndex + 1) % loadingMessages.length;
                loadingMessage.textContent = loadingMessages[currentMessageIndex];
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

    updateCompareButton();
});