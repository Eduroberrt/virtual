console.log('🟢 Modern Dashboard JavaScript loaded');

// Global variables
let countries = {};
let services = {};
let selectedCountry = null;
let selectedService = null;
let currentPrice = 0;

// Country flag mapping
const countryFlags = {
    'afghanistan': '🇦🇫', 'albania': '🇦🇱', 'algeria': '🇩🇿', 'angola': '🇦🇴', 'antiguaandbarbuda': '🇦🇬',
    'argentina': '🇦🇷', 'armenia': '🇦🇲', 'aruba': '🇦🇼', 'australia': '🇦🇺', 'austria': '🇦🇹',
    'azerbaijan': '🇦🇿', 'bahamas': '🇧🇸', 'bahrain': '🇧🇭', 'bangladesh': '🇧🇩', 'barbados': '🇧🇧',
    'belarus': '🇧🇾', 'belgium': '🇧🇪', 'belize': '🇧🇿', 'benin': '🇧🇯', 'bhutane': '🇧🇹',
    'bih': '🇧🇦', 'bolivia': '🇧🇴', 'botswana': '🇧🇼', 'brazil': '🇧🇷', 'bulgaria': '🇧🇬',
    'burkinafaso': '🇧🇫', 'burundi': '🇧🇮', 'cambodia': '🇰🇭', 'cameroon': '🇨🇲', 'canada': '🇨🇦',
    'capeverde': '🇨🇻', 'chad': '🇹🇩', 'chile': '🇨🇱', 'colombia': '🇨🇴', 'comoros': '🇰🇲',
    'congo': '🇨🇬', 'costarica': '🇨🇷', 'croatia': '🇭🇷', 'cyprus': '🇨🇾', 'czech': '🇨🇿',
    'denmark': '🇩🇰', 'djibouti': '🇩🇯', 'dominicana': '🇩🇴', 'easttimor': '🇹🇱', 'ecuador': '🇪🇨',
    'egypt': '🇪🇬', 'england': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'equatorialguinea': '🇬🇶', 'estonia': '🇪🇪', 'ethiopia': '🇪🇹',
    'finland': '🇫🇮', 'france': '🇫🇷', 'frenchguiana': '🇬🇫', 'gabon': '🇬🇦', 'gambia': '🇬🇲',
    'georgia': '🇬🇪', 'germany': '🇩🇪', 'ghana': '🇬🇭', 'gibraltar': '🇬🇮', 'greece': '🇬🇷',
    'guadeloupe': '🇬🇵', 'guatemala': '🇬🇹', 'guinea': '🇬🇳', 'guineabissau': '🇬🇼', 'guyana': '🇬🇾',
    'haiti': '🇭🇹', 'honduras': '🇭🇳', 'hongkong': '🇭🇰', 'hungary': '🇭🇺', 'india': '🇮🇳',
    'indonesia': '🇮🇩', 'ireland': '🇮🇪', 'israel': '🇮🇱', 'italy': '🇮🇹', 'ivorycoast': '🇨🇮',
    'jamaica': '🇯🇲', 'jordan': '🇯🇴', 'kazakhstan': '🇰🇿', 'kenya': '🇰🇪', 'kuwait': '🇰🇼',
    'kyrgyzstan': '🇰🇬', 'laos': '🇱🇦', 'latvia': '🇱🇻', 'lebanon': '🇱🇧', 'lesotho': '🇱🇸',
    'liberia': '🇱🇷', 'lithuania': '🇱🇹', 'luxembourg': '🇱🇺', 'macau': '🇲🇴', 'madagascar': '🇲🇬',
    'malawi': '🇲🇼', 'malaysia': '🇲🇾', 'maldives': '🇲🇻', 'mauritania': '🇲🇷', 'mauritius': '🇲🇺',
    'mexico': '🇲🇽', 'moldova': '🇲🇩', 'mongolia': '🇲🇳', 'montenegro': '🇲🇪', 'morocco': '🇲🇦',
    'mozambique': '🇲🇿', 'namibia': '🇳🇦', 'nepal': '🇳🇵', 'netherlands': '🇳🇱', 'newcaledonia': '🇳🇨',
    'newzealand': '🇳🇿', 'nicaragua': '🇳🇮', 'nigeria': '🇳🇬', 'northmacedonia': '🇲🇰', 'norway': '🇳🇴',
    'oman': '🇴🇲', 'pakistan': '🇵🇰', 'panama': '🇵🇦', 'papuanewguinea': '🇵🇬', 'paraguay': '🇵🇾',
    'peru': '🇵🇪', 'philippines': '🇵🇭', 'poland': '🇵🇱', 'portugal': '🇵🇹', 'puertorico': '🇵🇷',
    'reunion': '🇷🇪', 'romania': '🇷🇴', 'russia': '🇷🇺', 'rwanda': '🇷🇼', 'saintkittsandnevis': '🇰🇳',
    'saintlucia': '🇱🇨', 'saintvincentandgrenadines': '🇻🇨', 'salvador': '🇸🇻', 'samoa': '🇼🇸',
    'saudiarabia': '🇸🇦', 'senegal': '🇸🇳', 'serbia': '🇷🇸', 'seychelles': '🇸🇨', 'sierraleone': '🇸🇱',
    'singapore': '🇸🇬', 'slovakia': '🇸🇰', 'slovenia': '🇸🇮', 'solomonislands': '🇸🇧', 'southafrica': '🇿🇦',
    'spain': '🇪🇸', 'srilanka': '🇱🇰', 'suriname': '🇸🇷', 'swaziland': '🇸🇿', 'sweden': '🇸🇪',
    'taiwan': '🇹🇼', 'tajikistan': '🇹🇯', 'tanzania': '🇹🇿', 'thailand': '🇹🇭', 'tit': '🇹🇹',
    'togo': '🇹🇬', 'tunisia': '🇹🇳', 'turkmenistan': '🇹🇲', 'uganda': '🇺🇬', 'ukraine': '🇺🇦',
    'uruguay': '🇺🇾', 'usa': '🇺🇸', 'uzbekistan': '🇺🇿', 'venezuela': '🇻🇪', 'vietnam': '🇻🇳',
    'zambia': '🇿🇲'
};

function getCountryFlag(countryCode) {
    return countryFlags[countryCode.toLowerCase()] || '🏳️';
}

async function loadCountries() {
    try {
        const response = await fetch('/api/5sim/countries/');
        const data = await response.json();
        if (data.success && data.countries) countries = data.countries;
        else console.error('❌ Failed to load countries:', data.error);
    } catch (error) {
        console.error('❌ Error loading countries:', error);
    }
}

async function loadServices() {
    try {
        const response = await fetch('/api/5sim/products-list/');
        const data = await response.json();
        if (data.success && data.products) services = data.products;
        else console.error('Failed to load services:', data.error);
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

function populateCustomDropdown(type, data, searchTerm = '') {
    const containerId = type === 'country' ? 'countryOptions' : 'serviceOptions';
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    let filteredData = Object.entries(data).filter(([, name]) => name.toLowerCase().includes(searchTerm.toLowerCase()));
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
        option.innerHTML = type === 'country' ? `<span style="margin-right: 8px; font-size: 12px;">${getCountryFlag(code)}</span> ${name}` : name;
        option.dataset.value = code;
        option.dataset.name = name;
        option.addEventListener('mouseenter', () => option.style.backgroundColor = '#f8f9fa');
        option.addEventListener('mouseleave', () => option.style.backgroundColor = 'white');
        option.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (type === 'country') selectCountry(code, name);
            else selectService(code, name);
        });
        container.appendChild(option);
    });
}

function selectCountry(code, name) {
    selectedCountry = { code, name };
    document.getElementById('countryDropdownSelected').innerHTML = `<span style="margin-right: 8px;">${getCountryFlag(code)}</span> ${name}`;
    closeDropdown('country');
    selectedService = null;
    const serviceSelected = document.getElementById('serviceDropdownSelected');
    serviceSelected.textContent = 'Choose a service...';
    serviceSelected.style.color = '#333';
    populateCustomDropdown('service', services, '');
}

function selectService(code, name) {
    selectedService = { code, name };
    document.getElementById('serviceDropdownSelected').textContent = name;
    closeDropdown('service');
    if (selectedCountry) loadOperators(selectedCountry.code, code);
}

async function loadOperators(country, product) {
    if (!country || !product) return;
    try {
        const response = await fetch(`/api/5sim/prices/${country}/${product}/`);
        const data = await response.json();
        if (data.success && data.prices) {
            const validOperators = Object.entries(data.prices).filter(([, p]) => parseFloat(p.cost || p.price || 0) > 0 && parseInt(p.count || 0) > 0);
            if (validOperators.length > 0) {
                document.getElementById('operatorError').style.display = 'none';
                autoSelectCheapestOperator(country, product, data.prices);
            } else {
                document.getElementById('operatorError').style.display = 'block';
                resetPurchaseButton();
            }
        } else {
            document.getElementById('operatorError').style.display = 'block';
            resetPurchaseButton();
        }
    } catch (error) {
        document.getElementById('operatorError').style.display = 'block';
        resetPurchaseButton();
    }
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
    if (cheapest) updatePurchaseButton(country, product, cheapest.operator, minPrice);
    else {
        document.getElementById('operatorError').style.display = 'block';
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
            await loadRecentOrders();
            resetPurchaseButton();
        } else {
            showError(data.error || 'Purchase failed');
            purchaseBtn.classList.remove('loading');
            purchaseBtn.disabled = false;
            purchaseBtn.textContent = `Buy ₦${currentPrice || 0}`;
        }
    } catch (error) {
        showError('Network error during purchase');
        purchaseBtn.classList.remove('loading');
        purchaseBtn.disabled = false;
        purchaseBtn.textContent = `Buy ₦${currentPrice || 0}`;
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
}

function displayRecentOrders(orders) {
    const tableBody = document.querySelector('#recentOrdersTable tbody');
    if (!tableBody) return;
    if (!orders || orders.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted"><i class="fas fa-inbox"></i> No recent orders found</td></tr>`;
        return;
    }
    tableBody.innerHTML = orders.map(order => `
        <tr data-order-id="${order.id}">
            <td>${services[order.product] || order.product}</td>
            <td>${getCountryFlag(order.country)}</td>
            <td class="copyable-phone" data-copy="${order.phone_number || ''}">${order.phone_number || 'N/A'}</td>
            <td class="countdown-timer ${order.sms_code ? 'completed' : ''}" data-expires="${order.expires_at}" data-has-code="${!!order.sms_code}">${getTTLDisplay(order)}</td>
            <td class="code-column copyable-code" data-copy="${order.sms_code || ''}">${getCodeDisplay(order)}</td>
            <td class="status-column">${getStatusButton(order)}</td>
        </tr>
    `).join('');
    startCountdownTimers();
    addCopyFunctionality();
}

function addCopyFunctionality() {
    document.querySelectorAll('.copyable-phone, .copyable-code').forEach(el => {
        el.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            if (textToCopy && textToCopy.trim()) {
                copyToClipboard(textToCopy, this.classList.contains('copyable-phone') ? 'Phone number copied!' : 'Code copied!');
            }
        });
    });
}

async function copyToClipboard(text, successMessage) {
    try {
        await navigator.clipboard.writeText(text);
        showCopyNotification(successMessage);
    } catch {
        showCopyNotification('Copy failed. Please try again.', 'error');
    }
}

function showCopyNotification(message, type = 'success') {
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

function getTTLDisplay(order) {
    if (order.sms_code) return '✅';
    if (!order.expires_at) return '--:--';
    const diff = new Date(order.expires_at) - new Date();
    if (diff <= 0) return 'EXPIRED';
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function getCodeDisplay(order) {
    if (order.sms_code) return `<span class="code-text text-success fw-bold">${order.sms_code.trim()}</span>`;
    if (['PENDING', 'RECEIVED', 'FINISHED'].includes(order.status)) return `<div class="loading-spinner"></div>`;
    return '<span class="text-muted">--</span>';
}

function getStatusButton(order) {
    if (order.sms_code) return '<span class="status-success">Success</span>';
    if (['PENDING', 'RECEIVED'].includes(order.status)) return `<button class="status-cancel" onclick="cancelOrder('${order.id}')">Cancel</button>`;
    if (order.status === 'FINISHED') return '<span class="status-finished">Finished</span>';
    return `<span class="status-cancel">${order.status || 'Completed'}</span>`;
}

function startCountdownTimers() {
    document.querySelectorAll('.countdown-timer[data-expires]').forEach(el => {
        if (el.intervalId) clearInterval(el.intervalId);
        if (el.dataset.hasCode === 'true') return;
        const updateTimer = () => {
            const diff = new Date(el.dataset.expires) - new Date();
            if (diff <= 0) {
                clearInterval(el.intervalId);
                el.closest('tr')?.remove();
                checkEmptyTable();
            } else {
                const minutes = Math.floor(diff / 60000);
                const seconds = Math.floor((diff % 60000) / 1000);
                el.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }
        };
        updateTimer();
        el.intervalId = setInterval(updateTimer, 1000);
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

let activeDropdown = null;
function setupDropdown(type) {
    const selected = document.getElementById(`${type}DropdownSelected`);
    const container = document.getElementById(`${type}DropdownContainer`);
    const search = document.getElementById(`${type}Search`);
    if (!selected || !container || !search) return;
    selected.addEventListener('click', (e) => {
        e.stopPropagation();
        if (activeDropdown === type) closeDropdown(type);
        else openDropdown(type);
    });
    search.addEventListener('input', () => populateCustomDropdown(type, type === 'country' ? countries : services, search.value));
    container.addEventListener('click', e => e.stopPropagation());
}

function openDropdown(type) {
    if (activeDropdown && activeDropdown !== type) closeDropdown(activeDropdown);
    activeDropdown = type;
    document.getElementById(`${type}DropdownContainer`).classList.add('open');
    document.getElementById(`${type}DropdownSelected`).classList.add('open');
    populateCustomDropdown(type, type === 'country' ? countries : services, '');
    if (!/Android/i.test(navigator.userAgent)) document.getElementById(`${type}Search`).focus();
    document.addEventListener('click', handleOutsideClick);
}

function closeDropdown(type) {
    if (!type) return;
    document.getElementById(`${type}DropdownContainer`).classList.remove('open');
    document.getElementById(`${type}DropdownSelected`).classList.remove('open');
    document.getElementById(`${type}Search`).value = '';
    if (activeDropdown === type) activeDropdown = null;
    document.removeEventListener('click', handleOutsideClick);
}

function handleOutsideClick(e) {
    if (activeDropdown) {
        const container = document.getElementById(`${activeDropdown}DropdownContainer`);
        if (container && !container.contains(e.target)) closeDropdown(activeDropdown);
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
            await loadRecentOrders();
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
        audio.play().catch(() => {});
    } catch (e) {}
}

async function checkActiveOrdersForSMS() {
    const orderRows = document.querySelectorAll('#recentOrdersTable tr[data-order-id]');
    if (orderRows.length === 0) return;

    for (const row of orderRows) {
        // Only check orders that are still showing a loader
        if (row.querySelector('.code-column .loading-spinner')) {
            const orderId = row.getAttribute('data-order-id');
            if (orderId) {
                checkOrderSMSUpdate(orderId, row);
            }
        }
    }
}

// *** THIS IS THE FINAL, CORRECTED FUNCTION ***
async function checkOrderSMSUpdate(orderId, row) {
    try {
        const response = await fetch(`/api/5sim/order/${orderId}/status/`);
        const data = await response.json();

        // If the API call fails or there's no code, do nothing.
        if (!data.success || !data.sms_code) {
            // If the order has a final status (like TIMEOUT), refresh the whole list
            if (data.status && ['CANCELLED', 'FINISHED', 'TIMEOUT'].includes(data.status)) {
                await loadRecentOrders();
            }
            return;
        }

        // SUCCESS! The code is in the response. Update the UI directly.
        const smsCode = data.sms_code.trim();
        console.log(`✅ SMS Code Received: ${smsCode} for order ${orderId}. Updating UI.`);

        const codeCell = row.querySelector('.code-column');
        const timerCell = row.querySelector('.countdown-timer');
        const statusCell = row.querySelector('.status-column');

        if (codeCell) {
            codeCell.innerHTML = `<span class="code-text text-success fw-bold">${smsCode}</span>`;
            codeCell.setAttribute('data-copy', smsCode);
        }
        if (timerCell) {
            if (timerCell.intervalId) clearInterval(timerCell.intervalId);
            timerCell.innerHTML = '✅';
            timerCell.setAttribute('data-has-code', 'true');
        }
        if (statusCell) {
            statusCell.innerHTML = '<span class="status-success">Success</span>';
        }

        showSuccess(`SMS code received: ${smsCode}`);
        playNotificationSound();

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
    await loadRecentOrders();
    // Start the polling loop
    setInterval(checkActiveOrdersForSMS, 5000);
    // Start the cleanup loop for expired orders
    setInterval(cleanupExpiredOrders, 30000);
    console.log('✅ Dashboard initialization complete');
}

window.cancelOrder = cancelOrder;
document.addEventListener('DOMContentLoaded', initialize);