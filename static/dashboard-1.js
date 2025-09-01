console.log('🟢 Modern Dashboard JavaScript loaded');

// Global variables
let countries = {};
let services = {};
let selectedCountry = null;
let selectedService = null;
let currentPrice = 0;

// Country flag mapping
const countryFlags = {
    'afghanistan': '🇦🇫',
    'albania': '🇦🇱',
    'algeria': '🇩🇿',
    'angola': '🇦🇴',
    'antiguaandbarbuda': '🇦🇬',
    'argentina': '🇦🇷',
    'armenia': '🇦🇲',
    'aruba': '🇦🇼',
    'australia': '🇦🇺',
    'austria': '🇦🇹',
    'azerbaijan': '🇦🇿',
    'bahamas': '🇧🇸',
    'bahrain': '🇧🇭',
    'bangladesh': '🇧🇩',
    'barbados': '🇧🇧',
    'belarus': '🇧🇾',
    'belgium': '🇧🇪',
    'belize': '🇧🇿',
    'benin': '🇧🇯',
    'bhutane': '🇧🇹',
    'bih': '🇧🇦',
    'bolivia': '🇧🇴',
    'botswana': '🇧🇼',
    'brazil': '🇧🇷',
    'bulgaria': '🇧🇬',
    'burkinafaso': '🇧🇫',
    'burundi': '🇧🇮',
    'cambodia': '🇰🇭',
    'cameroon': '🇨🇲',
    'canada': '🇨🇦',
    'capeverde': '🇨🇻',
    'chad': '🇹🇩',
    'chile': '🇨🇱',
    'colombia': '🇨🇴',
    'comoros': '🇰🇲',
    'congo': '🇨🇬',
    'costarica': '🇨🇷',
    'croatia': '🇭🇷',
    'cyprus': '🇨🇾',
    'czech': '🇨🇿',
    'denmark': '🇩🇰',
    'djibouti': '🇩🇯',
    'dominicana': '🇩🇴',
    'easttimor': '🇹🇱',
    'ecuador': '🇪🇨',
    'egypt': '🇪🇬',
    'england': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'equatorialguinea': '🇬🇶',
    'estonia': '🇪🇪',
    'ethiopia': '🇪🇹',
    'finland': '🇫🇮',
    'france': '🇫🇷',
    'frenchguiana': '🇬🇫',
    'gabon': '🇬🇦',
    'gambia': '🇬🇲',
    'georgia': '🇬🇪',
    'germany': '🇩🇪',
    'ghana': '🇬🇭',
    'gibraltar': '🇬🇮',
    'greece': '🇬🇷',
    'guadeloupe': '🇬🇵',
    'guatemala': '🇬🇹',
    'guinea': '🇬🇳',
    'guineabissau': '🇬🇼',
    'guyana': '🇬🇾',
    'haiti': '🇭🇹',
    'honduras': '🇭🇳',
    'hongkong': '🇭🇰',
    'hungary': '🇭🇺',
    'india': '🇮🇳',
    'indonesia': '🇮🇩',
    'ireland': '🇮🇪',
    'israel': '🇮🇱',
    'italy': '🇮🇹',
    'ivorycoast': '🇨🇮',
    'jamaica': '🇯🇲',
    'jordan': '🇯🇴',
    'kazakhstan': '🇰🇿',
    'kenya': '🇰🇪',
    'kuwait': '🇰🇼',
    'kyrgyzstan': '🇰🇬',
    'laos': '🇱🇦',
    'latvia': '🇱🇻',
    'lebanon': '🇱🇧',
    'lesotho': '🇱🇸',
    'liberia': '🇱🇷',
    'lithuania': '🇱🇹',
    'luxembourg': '🇱🇺',
    'macau': '🇲🇴',
    'madagascar': '🇲🇬',
    'malawi': '🇲🇼',
    'malaysia': '🇲🇾',
    'maldives': '🇲🇻',
    'mauritania': '🇲🇷',
    'mauritius': '🇲🇺',
    'mexico': '🇲🇽',
    'moldova': '🇲🇩',
    'mongolia': '🇲🇳',
    'montenegro': '🇲🇪',
    'morocco': '🇲🇦',
    'mozambique': '🇲🇿',
    'namibia': '🇳🇦',
    'nepal': '🇳🇵',
    'netherlands': '🇳🇱',
    'newcaledonia': '🇳🇨',
    'newzealand': '🇳🇿',
    'nicaragua': '🇳🇮',
    'nigeria': '🇳🇬',
    'northmacedonia': '🇲🇰',
    'norway': '🇳🇴',
    'oman': '🇴🇲',
    'pakistan': '🇵🇰',
    'panama': '🇵🇦',
    'papuanewguinea': '🇵🇬',
    'paraguay': '🇵🇾',
    'peru': '🇵🇪',
    'philippines': '🇵🇭',
    'poland': '🇵🇱',
    'portugal': '🇵🇹',
    'puertorico': '🇵🇷',
    'reunion': '🇷🇪',
    'romania': '🇷🇴',
    'russia': '🇷🇺',
    'rwanda': '🇷🇼',
    'saintkittsandnevis': '🇰🇳',
    'saintlucia': '🇱🇨',
    'saintvincentandgrenadines': '🇻🇨',
    'salvador': '🇸🇻',
    'samoa': '🇼🇸',
    'saudiarabia': '🇸🇦',
    'senegal': '🇸🇳',
    'serbia': '🇷🇸',
    'seychelles': '🇸🇨',
    'sierraleone': '🇸🇱',
    'singapore': '🇸🇬',
    'slovakia': '🇸🇰',
    'slovenia': '🇸🇮',
    'solomonislands': '🇸🇧',
    'southafrica': '🇿🇦',
    'spain': '🇪🇸',
    'srilanka': '🇱🇰',
    'suriname': '🇸🇷',
    'swaziland': '🇸🇿',
    'sweden': '🇸🇪',
    'taiwan': '🇹🇼',
    'tajikistan': '🇹🇯',
    'tanzania': '🇹🇿',
    'thailand': '🇹🇭',
    'tit': '🇹🇹',  // Assuming this is Trinidad and Tobago
    'togo': '🇹🇬',
    'tunisia': '🇹🇳',
    'turkmenistan': '🇹🇲',
    'uganda': '🇺🇬',
    'ukraine': '🇺🇦',
    'uruguay': '🇺🇾',
    'usa': '🇺🇸',
    'uzbekistan': '🇺🇿',
    'venezuela': '🇻🇪',
    'vietnam': '🇻🇳',
    'zambia': '🇿🇲'
};

// Function to get country flag
function getCountryFlag(countryCode) {
    return countryFlags[countryCode.toLowerCase()] || '🏳️';
}

// Load countries from API
async function loadCountries() {
    try {
        console.log('🔄 Loading countries from API...');
        const response = await fetch('/api/5sim/countries/');
        const data = await response.json();
        
        if (data.success && data.countries) {
            countries = data.countries;
            console.log('✅ Countries loaded from API:', Object.keys(countries).length);
        } else {
            console.error('❌ Failed to load countries:', data.error);
        }
    } catch (error) {
        console.error('❌ Error loading countries:', error);
    }
}

// Load services from API
async function loadServices() {
    try {
        const response = await fetch('/api/5sim/products-list/');
        const data = await response.json();
        
        if (data.success && data.products) {
            services = data.products;
            console.log('Services loaded:', Object.keys(services).length);
        } else {
            console.error('Failed to load services:', data.error);
        }
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

// Populate country dropdown
function populateCountryDropdown() {
    populateCustomDropdown('country', countries, '');
}

// Populate service dropdown (when country is selected)
function populateServiceDropdown() {
    if (!selectedCountry) return;
    
    populateCustomDropdown('service', services, '');
    
    // Enable service dropdown
    const serviceSelected = document.getElementById('serviceDropdownSelected');
    serviceSelected.textContent = 'Choose a service...';
    serviceSelected.style.color = '#333';
}

// Generic function to populate custom dropdown with search
function populateCustomDropdown(type, data, searchTerm = '') {
    const containerId = type === 'country' ? 'countryOptions' : 'serviceOptions';
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    let filteredData = Object.entries(data).filter(([code, name]) => 
        name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    filteredData.sort((a, b) => a[1].localeCompare(b[1]));
    
    if (filteredData.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'dropdown-option';
        noResults.style.cssText = 'color: #999; text-align: center; cursor: default;';
        noResults.textContent = 'No results found';
        container.appendChild(noResults);
        return;
    }
    
    filteredData.forEach(([code, name]) => {
        const option = document.createElement('div');
        option.className = 'dropdown-option';
        option.style.cssText = 'font-size: 13px; cursor: pointer; padding: 8px 12px; display: flex; align-items: center; user-select: none;';
        
        if (type === 'country') {
            const flag = getCountryFlag(code);
            option.innerHTML = `<span style="margin-right: 8px; font-size: 12px;">${flag}</span> ${name}`;
        } else {
            option.textContent = name;
        }
        
        option.dataset.value = code;
        option.dataset.name = name;
        
        option.addEventListener('mouseenter', () => option.style.backgroundColor = '#f8f9fa');
        option.addEventListener('mouseleave', () => option.style.backgroundColor = 'white');
        
        const handleSelection = (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (type === 'country') {
                selectCountry(code, name);
            } else {
                selectService(code, name);
            }
        };
        
        option.addEventListener('click', handleSelection);
        
        container.appendChild(option);
    });
}

// Handle country selection
function selectCountry(code, name) {
    selectedCountry = { code, name };
    const flag = getCountryFlag(code);
    
    document.getElementById('countryDropdownSelected').innerHTML = `<span style="margin-right: 8px;">${flag}</span> ${name}`;
    closeDropdown('country');
    
    selectedService = null;
    populateServiceDropdown();
    
    console.log('Country selected:', name);
}

// Handle service selection
function selectService(code, name) {
    selectedService = { code, name };
    
    document.getElementById('serviceDropdownSelected').textContent = name;
    closeDropdown('service');
    
    console.log('Service selected:', name);
    
    if (selectedCountry) {
        loadOperators(selectedCountry.code, code);
    }
}

// Load operators for selected country and service
async function loadOperators(country, product) {
    if (!country || !product) return;

    try {
        const response = await fetch(`/api/5sim/prices/${country}/${product}/`);
        const data = await response.json();
        
        if (data.success && data.prices) {
            const validOperators = Object.entries(data.prices).filter(([_, priceData]) => {
                return parseFloat(priceData.cost || priceData.price || 0) > 0 && parseInt(priceData.count || 0) > 0;
            });
            
            if (validOperators.length > 0) {
                hideOperatorError();
                autoSelectCheapestOperator(country, product, data.prices);
            } else {
                showOperatorError();
                resetPurchaseButton();
            }
        } else {
            showOperatorError();
            resetPurchaseButton();
        }
    } catch (error) {
        showOperatorError();
        resetPurchaseButton();
    }
}

function showOperatorError() {
    const errorDiv = document.getElementById('operatorError');
    if (errorDiv) errorDiv.style.display = 'block';
}

function hideOperatorError() {
    const errorDiv = document.getElementById('operatorError');
    if (errorDiv) errorDiv.style.display = 'none';
}

function resetPurchaseButton() {
    const purchaseBtn = document.getElementById('purchaseBtn');
    if (purchaseBtn) {
        purchaseBtn.disabled = true;
        purchaseBtn.textContent = 'Select service';
        purchaseBtn.onclick = null;
    }
}

function autoSelectCheapestOperator(country, product, prices) {
    if (!prices || Object.keys(prices).length === 0) return;
    
    let cheapest = null;
    let minPrice = Infinity;
    
    Object.entries(prices).forEach(([operator, priceData]) => {
        const price = parseFloat(priceData.cost || priceData.price || 0);
        const count = parseInt(priceData.count || 0);
        
        if (price > 0 && count > 0 && price < minPrice) {
            minPrice = price;
            cheapest = { operator, ...priceData };
        }
    });
    
    if (cheapest) {
        updatePurchaseButton(country, product, cheapest.operator, minPrice);
    } else {
        showOperatorError();
        resetPurchaseButton();
    }
}

function updatePurchaseButton(country, product, operator, price) {
    const purchaseBtn = document.getElementById('purchaseBtn');
    if (purchaseBtn) {
        currentPrice = price;
        purchaseBtn.textContent = `Buy ₦${price}`;
        purchaseBtn.disabled = false;
        purchaseBtn.onclick = () => purchaseNumber(country, product, operator);
    }
}

function getCurrentPrice() {
    return currentPrice || 0;
}

async function purchaseNumber(country, product, operator) {
    const purchaseBtn = document.getElementById('purchaseBtn');
    purchaseBtn.classList.add('loading');
    purchaseBtn.disabled = true;
    purchaseBtn.innerHTML = '<div class="spinner"></div>Processing...';
    
    try {
        const formData = new FormData();
        formData.append('country', country);
        formData.append('product', product);
        formData.append('operator', operator);
        
        const response = await fetch('/api/5sim/buy-activation/', {
            method: 'POST',
            headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`SMS number purchased successfully! Phone: ${data.phone_number}`);
            if (data.new_balance !== undefined) updateBalanceDisplay(data.new_balance);
            loadRecentOrders();
            resetPurchaseButton();
        } else {
            showError(data.error || 'Purchase failed');
            purchaseBtn.classList.remove('loading');
            purchaseBtn.disabled = false;
            purchaseBtn.textContent = `Buy ₦${getCurrentPrice()}`;
        }
    } catch (error) {
        showError('Network error during purchase');
        purchaseBtn.classList.remove('loading');
        purchaseBtn.disabled = false;
        purchaseBtn.textContent = `Buy ₦${getCurrentPrice()}`;
    }
}

async function loadRecentOrders() {
    try {
        const response = await fetch('/api/5sim/orders/');
        const data = await response.json();
        displayRecentOrders(data.success ? data.orders : []);
    } catch (error) {
        displayRecentOrders([]);
    }
}

function updateBalanceDisplay(newBalance) {
    const formattedBalance = `₦${parseFloat(newBalance).toFixed(2)}`;
    document.querySelectorAll('.balance-amount, .user-balance, [data-balance], #userBalance').forEach(el => {
        el.textContent = formattedBalance;
    });
    console.log(`Balance updated to: ${formattedBalance}`);
}

function displayRecentOrders(orders) {
    const tableBody = document.querySelector('#recentOrdersTable tbody');
    if (!tableBody) return;

    if (!orders || orders.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted"><i class="fas fa-inbox"></i> No recent orders found</td></tr>`;
        return;
    }

    tableBody.innerHTML = orders.map(order => {
        const countryFlag = getCountryFlag(order.country);
        const productName = services[order.product] || order.product;
        const ttlDisplay = getTTLDisplay(order.expires_at, order);
        const codeDisplay = getCodeDisplay(order);
        const statusButton = getStatusButton(order);

        return `
            <tr data-order-id="${order.id}">
                <td>${productName}</td>
                <td>${countryFlag}</td>
                <td class="copyable-phone" data-copy="${order.phone_number || ''}">${order.phone_number || 'N/A'}</td>
                <td class="countdown-timer ${order.sms_code ? 'completed' : ''}" data-expires="${order.expires_at}" data-has-code="${!!order.sms_code}">${ttlDisplay}</td>
                <td class="code-column copyable-code" data-copy="${order.sms_code || ''}">${codeDisplay}</td>
                <td class="status-column">${statusButton}</td>
            </tr>
        `;
    }).join('');

    startCountdownTimers();
    addCopyFunctionality();
}

function addCopyFunctionality() {
    document.querySelectorAll('.copyable-phone, .copyable-code').forEach(el => {
        el.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            if (textToCopy && textToCopy.trim()) {
                const message = this.classList.contains('copyable-phone') ? 'Phone number copied!' : 'Code copied!';
                copyToClipboard(textToCopy, message);
            }
        });
    });
}

async function copyToClipboard(text, successMessage) {
    try {
        await navigator.clipboard.writeText(text);
        showCopyNotification(successMessage);
    } catch (error) {
        showCopyNotification('Copy failed. Please try again.', 'error');
    }
}

function showCopyNotification(message, type = 'success') {
    document.querySelectorAll('.copy-notification').forEach(n => n.remove());
    const notification = document.createElement('div');
    notification.className = 'copy-notification';
    notification.textContent = message;
    notification.style.cssText = `position: fixed; top: 20px; right: 20px; background: ${type === 'success' ? '#28a745' : '#dc3545'}; color: white; padding: 8px 16px; border-radius: 4px; font-size: 14px; font-weight: 500; box-shadow: 0 2px 8px rgba(0,0,0,0.2); z-index: 10000; opacity: 0; transform: translateY(-10px); transition: all 0.3s ease;`;
    document.body.appendChild(notification);
    setTimeout(() => { notification.style.opacity = '1'; notification.style.transform = 'translateY(0)'; }, 10);
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-10px)';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

function getTTLDisplay(expiresAt, order) {
    if (order.sms_code) return '✅';
    if (!expiresAt) return '--:--';
    const diff = new Date(expiresAt) - new Date();
    if (diff <= 0) return 'EXPIRED';
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function getCodeDisplay(order) {
    if (order.sms_code) return `<span class="code-text text-success fw-bold">${order.sms_code.trim()}</span>`;
    if (order.status === 'PENDING' || order.status === 'RECEIVED' || order.status === 'FINISHED') return `<div class="loading-spinner"></div>`;
    return '<span class="text-muted">--</span>';
}

function getStatusButton(order) {
    if (order.sms_code) return '<span class="status-success">Success</span>';
    if (order.status === 'PENDING' || order.status === 'RECEIVED') return `<button class="status-cancel" onclick="cancelOrder('${order.id}')">Cancel</button>`;
    if (order.status === 'FINISHED') return '<span class="status-finished">Finished</span>';
    return '<span class="status-cancel">Completed</span>';
}

function startCountdownTimers() {
    document.querySelectorAll('.countdown-timer[data-expires]').forEach(el => {
        if (el.interval) clearInterval(el.interval);
        if (el.dataset.hasCode === 'true') return;

        const updateTimer = () => {
            const diff = new Date(el.dataset.expires) - new Date();
            if (diff <= 0) {
                clearInterval(el.interval);
                el.closest('tr')?.remove();
                checkEmptyTable();
            } else {
                const minutes = Math.floor(diff / 60000);
                const seconds = Math.floor((diff % 60000) / 1000);
                el.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }
        };
        updateTimer();
        el.interval = setInterval(updateTimer, 1000);
    });
}

function checkEmptyTable() {
    const tableBody = document.querySelector('#recentOrdersTable tbody');
    if (tableBody && tableBody.children.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4"><i class="fas fa-inbox fa-2x mb-3 d-block"></i>No active orders.</td></tr>`;
    }
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => errorDiv.style.display = 'none', 5000);
    }
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        setTimeout(() => successDiv.style.display = 'none', 5000);
    }
}

// --- NEW/REFACTORED DROPDOWN LOGIC ---
let activeDropdown = null;
let isSearchFocused = false;
let openTimeout;

function setupDropdown(type) {
    const selected = document.getElementById(`${type}DropdownSelected`);
    const container = document.getElementById(`${type}DropdownContainer`);
    const search = document.getElementById(`${type}Search`);
    const options = document.getElementById(`${type}Options`);

    if (!selected || !container || !search || !options) {
        console.error(`Missing elements for ${type} dropdown.`);
        return;
    }

    selected.addEventListener('click', (e) => {
        e.stopPropagation();
        if (activeDropdown === type) {
            closeDropdown(type);
        } else {
            openDropdown(type);
        }
    });

    search.addEventListener('input', () => {
        const data = type === 'country' ? countries : services;
        populateCustomDropdown(type, data, search.value);
    });

    // Android fix: Use mousedown to prevent blur from closing dropdown
    search.addEventListener('mousedown', () => {
        isSearchFocused = true;
    });
    search.addEventListener('blur', () => {
        isSearchFocused = false;
    });

    // Prevent clicks inside the container from closing it
    container.addEventListener('click', e => e.stopPropagation());
}

function openDropdown(type) {
    if (activeDropdown && activeDropdown !== type) {
        closeDropdown(activeDropdown);
    }

    activeDropdown = type;
    const container = document.getElementById(`${type}DropdownContainer`);
    const selected = document.getElementById(`${type}DropdownSelected`);
    const search = document.getElementById(`${type}Search`);

    container.classList.add('open');
    selected.classList.add('open');

    const data = type === 'country' ? countries : services;
    populateCustomDropdown(type, data, '');
    
    // Use a small timeout to prevent the keyboard from immediately closing the dropdown on Android
    setTimeout(() => {
        const isAndroid = /Android/i.test(navigator.userAgent);
        if (!isAndroid) {
            search.focus();
        }
    }, 100);

    // Add a slight delay before the outside click listener is fully active
    clearTimeout(openTimeout);
    openTimeout = setTimeout(() => {
        document.addEventListener('click', handleOutsideClick);
    }, 50);
}

function closeDropdown(type) {
    if (!type) return;
    const container = document.getElementById(`${type}DropdownContainer`);
    const selected = document.getElementById(`${type}DropdownSelected`);
    const search = document.getElementById(`${type}Search`);

    container.classList.remove('open');
    selected.classList.remove('open');
    search.value = '';

    if (activeDropdown === type) {
        activeDropdown = null;
    }
    document.removeEventListener('click', handleOutsideClick);
}

function handleOutsideClick(e) {
    // If search input is focused (especially on Android), don't close
    if (isSearchFocused) {
        return;
    }
    if (activeDropdown) {
        const container = document.getElementById(`${activeDropdown}DropdownContainer`);
        if (container && !container.contains(e.target)) {
            closeDropdown(activeDropdown);
        }
    }
}


async function cancelOrder(orderId) {
    try {
        const response = await fetch(`/api/5sim/order/${orderId}/cancel/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }
        });
        const data = await response.json();
        if (data.success) {
            showSuccess(`Order cancelled. Refund of ₦${data.refund_amount || 'amount'} credited.`);
            if (data.new_balance !== undefined) updateBalanceDisplay(data.new_balance);
            loadRecentOrders();
        } else {
            showError(data.error || 'Failed to cancel order');
        }
    } catch (error) {
        showError('Network error while cancelling order');
    }
}

function playNotificationSound() {
    try {
        const audio = new Audio('data:audio/mp3;base64,SUQzBAAAAAABEVRYWFgAAAAtAAADY29tbWVudABCaWdTb3VuZEJhbmsuY29tIC8gTGFTb25vdGhlcXVlLm9yZwBURU5DAAAAHQAAA1N3aXRjaCBQbHVzIMKpIE5DSCBTb2Z0d2FyZQBUSVQyAAAABgAAAzIyMzUAVFNTRQAAAA8AAANMYXZmNTcuODMuMTAwAAAAAAAAAAAAAAD/80DEAAAAA0gAAAAATEFNRTMuMTAwVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQsRbAAADSAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQMSkAAADSAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV');
        audio.volume = 0.5;
        audio.play().catch(e => console.log("Sound play failed:", e));
    } catch (e) {
        console.log('Could not play notification sound', e);
    }
}

async function checkActiveOrdersForSMS() {
    const orderRows = document.querySelectorAll('#recentOrdersTable tr[data-order-id]');
    if (orderRows.length === 0) return;

    for (const row of orderRows) {
        const hasCode = row.querySelector('.code-column .code-text');
        if (hasCode) continue;

        const orderId = row.getAttribute('data-order-id');
        checkOrderSMSUpdate(orderId, row);
    }
}

async function checkOrderSMSUpdate(orderId, row) {
    try {
        const response = await fetch(`/api/5sim/order/${orderId}/status/`);
        const data = await response.json();

        if (data.success) {
            let smsCode = null;
            if (data.sms_code) {
                smsCode = (data.sms_code.match(/(\d{4,8})/) || [])[1];
            } else if (data.sms && data.sms.length > 0) {
                smsCode = (data.sms[data.sms.length - 1].text.match(/(\d{4,8})/) || [])[1];
            }

            if (smsCode) {
                const codeCell = row.querySelector('.code-column');
                const timerCell = row.querySelector('.countdown-timer');
                const statusCell = row.querySelector('.status-column');

                codeCell.innerHTML = `<span class="code-text text-success fw-bold">${smsCode}</span>`;
                codeCell.setAttribute('data-copy', smsCode);
                timerCell.innerHTML = '✅';
                timerCell.setAttribute('data-has-code', 'true');
                statusCell.innerHTML = '<span class="status-success">Success</span>';
                
                if (timerCell.interval) clearInterval(timerCell.interval);
                
                showSuccess(`SMS code received: ${smsCode}`);
                playNotificationSound();
            }
        }
    } catch (error) {
        console.error(`Error checking SMS for order ${orderId}:`, error);
    }
}

function cleanupExpiredOrders() {
    document.querySelectorAll('.countdown-timer[data-expires]').forEach(el => {
        if (el.dataset.hasCode === 'true') return;
        const diff = new Date(el.dataset.expires) - new Date();
        if (diff <= 0) {
            el.closest('tr')?.remove();
            checkEmptyTable();
        }
    });
}

async function initialize() {
    console.log('🚀 Initializing dashboard...');
    await Promise.all([loadCountries(), loadServices()]);
    
    setupDropdown('country');
    setupDropdown('service');
    
    loadRecentOrders();
    
    setInterval(loadRecentOrders, 10000);
    setInterval(checkActiveOrdersForSMS, 5000);
    setInterval(cleanupExpiredOrders, 30000);
    
    console.log('✅ Dashboard initialization complete');
}

window.cancelOrder = cancelOrder;
document.addEventListener('DOMContentLoaded', initialize);