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
        const response = await fetch('/api/5sim/countries/');
        const data = await response.json();
        
        if (data.success && data.countries) {
            countries = data.countries;
            populateCountryDropdown();
            console.log('Countries loaded:', Object.keys(countries).length);
        } else {
            console.error('Failed to load countries:', data.error);
        }
    } catch (error) {
        console.error('Error loading countries:', error);
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
    
    // Filter data based on search term
    let filteredData = Object.entries(data).filter(([code, name]) => 
        name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    // Sort alphabetically by name (especially important for services)
    filteredData.sort((a, b) => a[1].localeCompare(b[1]));
    
    if (filteredData.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'dropdown-option';
        noResults.style.color = '#999';
        noResults.style.textAlign = 'center';
        noResults.style.cursor = 'default';
        noResults.textContent = 'No results found';
        container.appendChild(noResults);
        return;
    }
    
    filteredData.forEach(([code, name]) => {
        const option = document.createElement('div');
        option.className = 'dropdown-option';
        option.style.fontSize = '13px';
        option.style.cursor = 'pointer';
        option.style.padding = '8px 12px';
        option.style.display = 'flex';
        option.style.alignItems = 'center';
        option.style.userSelect = 'none';
        
        // Add flag for countries
        if (type === 'country') {
            const flag = getCountryFlag(code);
            option.innerHTML = `<span style="margin-right: 8px; font-size: 12px;">${flag}</span> ${name}`;
        } else {
            option.textContent = name;
        }
        
        option.dataset.value = code;
        option.dataset.name = name;
        
        // Add hover effects
        option.addEventListener('mouseenter', () => {
            option.style.backgroundColor = '#f8f9fa';
        });
        
        option.addEventListener('mouseleave', () => {
            option.style.backgroundColor = 'white';
        });
        
        // Enhanced click handler with multiple event types
        const handleSelection = (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log(`${type} option clicked:`, name, code);
            
            if (type === 'country') {
                selectCountry(code, name);
            } else {
                selectService(code, name);
            }
        };
        
        option.addEventListener('click', handleSelection);
        option.addEventListener('mousedown', handleSelection);
        option.addEventListener('touchstart', handleSelection);
        
        container.appendChild(option);
    });
}

// Handle country selection
function selectCountry(code, name) {
    selectedCountry = { code, name };
    const flag = getCountryFlag(code);
    
    // Update custom dropdown
    document.getElementById('countryDropdownSelected').innerHTML = `<span style="margin-right: 8px;">${flag}</span> ${name}`;
    document.getElementById('countryDropdownContainer').classList.remove('open');
    document.getElementById('countryDropdownSelected').classList.remove('open');
    document.getElementById('countrySearch').value = '';
    
    // Remove backdrop
    const backdrop = document.getElementById('country-dropdown-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
    
    // Remove body class when selection is made
    document.body.classList.remove('country-dropdown-open');
    
    // Restore service elements
    const serviceSelected = document.getElementById('serviceDropdownSelected');
    const serviceContainer = document.getElementById('serviceDropdownContainer');
    if (serviceSelected && serviceContainer) {
        serviceSelected.style.display = '';
        serviceContainer.style.display = '';
    }
    
    // Reset service selection
    selectedService = null;
    
    // Enable and populate service dropdown
    populateServiceDropdown();
    
    console.log('Country selected:', name);
}

// Handle service selection
function selectService(code, name) {
    selectedService = { code, name };
    
    // Update custom dropdown
    document.getElementById('serviceDropdownSelected').textContent = name;
    document.getElementById('serviceDropdownContainer').classList.remove('open');
    document.getElementById('serviceDropdownSelected').classList.remove('open');
    document.getElementById('serviceSearch').value = '';
    
    // Remove backdrop
    const backdrop = document.getElementById('service-dropdown-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
    
    console.log('Service selected:', name);
    
    // Load operators/pricing for this country + service combination
    if (selectedCountry) {
        loadOperators(selectedCountry.code, code);
    }
}

// Load operators for selected country and service
async function loadOperators(country, product) {
    if (!country || !product) {
        return;
    }

    try {
        const response = await fetch(`/api/5sim/prices/${country}/${product}/`);
        const data = await response.json();
        
        if (data.success && data.prices) {
            // Check if there are any operators with valid pricing and available phones
            const validOperators = Object.entries(data.prices).filter(([operator, priceData]) => {
                const price = parseFloat(priceData.cost || priceData.price || 0);
                const count = parseInt(priceData.count || 0);
                return price > 0 && count > 0; // Both price and available count must be > 0
            });
            
            if (validOperators.length > 0) {
                // Hide error message and auto-select cheapest operator with available phones
                hideOperatorError();
                autoSelectCheapestOperator(country, product, data.prices);
            } else {
                // Show error message for no available operators
                showOperatorError();
                resetPurchaseButton();
            }
        } else {
            console.error('No pricing data available');
            showOperatorError();
            resetPurchaseButton();
        }
    } catch (error) {
        console.error('Failed to load operators:', error);
        showOperatorError();
        resetPurchaseButton();
    }
}

// Show error message when no operators available
function showOperatorError() {
    const errorDiv = document.getElementById('operatorError');
    if (errorDiv) {
        errorDiv.style.display = 'block';
    }
}

// Hide operator error message
function hideOperatorError() {
    const errorDiv = document.getElementById('operatorError');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Reset purchase button to disabled state
function resetPurchaseButton() {
    const purchaseBtn = document.getElementById('purchaseBtn');
    if (purchaseBtn) {
        purchaseBtn.disabled = true;
        purchaseBtn.textContent = 'Select service';
        purchaseBtn.onclick = null;
    }
}

// Auto-select cheapest operator with available phones
function autoSelectCheapestOperator(country, product, prices) {
    if (!prices || Object.keys(prices).length === 0) {
        return;
    }
    
    // Find cheapest option with available phones
    let cheapest = null;
    let minPrice = Infinity;
    
    Object.entries(prices).forEach(([operator, priceData]) => {
        const price = parseFloat(priceData.cost || priceData.price || 0);
        const count = parseInt(priceData.count || 0);
        
        // Only consider operators with available phones (count > 0) and valid price
        if (price > 0 && count > 0 && price < minPrice) {
            minPrice = price;
            cheapest = { operator, ...priceData };
        }
    });
    
    if (cheapest) {
        console.log(`Auto-selected cheapest with availability: ${cheapest.operator} - $${minPrice} (${cheapest.count || 0} available)`);
        
        // Update purchase button or display pricing info
        updatePurchaseButton(country, product, cheapest.operator, minPrice);
    } else {
        console.log('No operators available with both pricing and phone availability');
        showOperatorError();
        resetPurchaseButton();
    }
}

// Update purchase button with selected service info
function updatePurchaseButton(country, product, operator, price) {
    const purchaseBtn = document.getElementById('purchaseBtn');
    if (purchaseBtn) {
        currentPrice = price; // Store current price
        purchaseBtn.textContent = `Buy ₦${price}`;
        purchaseBtn.disabled = false;
        purchaseBtn.onclick = () => {
            purchaseNumber(country, product, operator);
        };
    }
}

// Get current price for button reset
function getCurrentPrice() {
    return currentPrice || 0;
}

// Purchase number function
async function purchaseNumber(country, product, operator) {
    const purchaseBtn = document.getElementById('purchaseBtn');
    
    try {
        // Add loading state
        purchaseBtn.classList.add('loading');
        purchaseBtn.disabled = true;
        purchaseBtn.innerHTML = '<div class="spinner"></div>Processing...';
        
        // Prepare form data for the purchase
        const formData = new FormData();
        formData.append('country', country);
        formData.append('product', product);
        formData.append('operator', operator);
        
        const response = await fetch('/api/5sim/buy-activation/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Purchase successful:', data);
            showSuccess(`SMS number purchased successfully! Phone: ${data.phone_number}`);
            
            // Update user balance immediately
            if (data.new_balance !== undefined) {
                updateBalanceDisplay(data.new_balance);
            }
            
            // Refresh orders table immediately
            loadRecentOrders();
            
            // Reset button to initial state
            purchaseBtn.classList.remove('loading');
            purchaseBtn.disabled = true;
            purchaseBtn.textContent = 'Select service';
        } else {
            console.error('Purchase failed:', data.error);
            showError(data.error || 'Purchase failed');
            
            // Reset button to previous state
            purchaseBtn.classList.remove('loading');
            purchaseBtn.disabled = false;
            purchaseBtn.textContent = `Buy ₦${getCurrentPrice()}`;
        }
    } catch (error) {
        console.error('Purchase error:', error);
        showError('Network error during purchase');
        
        // Reset button to previous state
        purchaseBtn.classList.remove('loading');
        purchaseBtn.disabled = false;
        purchaseBtn.textContent = `Buy ₦${getCurrentPrice()}`;
    }
}

// Load recent orders
async function loadRecentOrders() {
    try {
        const response = await fetch('/api/5sim/orders/');
        const data = await response.json();
        
        if (data.success && data.orders) {
            displayRecentOrders(data.orders);
            console.log(`Loaded ${data.orders.length} recent orders`);
        } else {
            console.log('No recent orders found');
            displayRecentOrders([]);
        }
    } catch (error) {
        console.error('Failed to load recent orders:', error);
        displayRecentOrders([]);
    }
}

// Update balance display
function updateBalanceDisplay(newBalance) {
    // Try to update balance in the header or balance display area
    const balanceElements = document.querySelectorAll('.balance-amount, .user-balance, [data-balance], .balance-display, #userBalance');
    balanceElements.forEach(element => {
        if (element.dataset.balance !== undefined) {
            element.dataset.balance = newBalance;
        }
        element.textContent = `₦${parseFloat(newBalance).toFixed(2)}`;
    });
    
    // Also try to update any element that contains balance text
    const allElements = document.querySelectorAll('*');
    allElements.forEach(element => {
        if (element.textContent && element.textContent.includes('₦') && element.children.length === 0) {
            // Check if this looks like a balance display
            const balanceMatch = element.textContent.match(/₦[\d,]+\.?\d*/);
            if (balanceMatch) {
                element.textContent = element.textContent.replace(balanceMatch[0], `₦${parseFloat(newBalance).toFixed(2)}`);
            }
        }
    });
    
    console.log(`Balance updated to: ₦${parseFloat(newBalance).toFixed(2)}`);
}

// Display recent orders in table
function displayRecentOrders(orders) {
    const tableBody = document.querySelector('#recentOrdersTable tbody');
    
    if (!tableBody) {
        console.error('Recent orders table body not found');
        return;
    }
    
    if (!orders || orders.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="fas fa-inbox"></i> No recent orders found
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = orders.map(order => {
        const countryFlag = getCountryFlag(order.country);
        const productName = services[order.product] || order.product;
        
        // TTL countdown
        const ttlDisplay = getTTLDisplay(order.expires_at, order);
        
        // Code display
        const codeDisplay = getCodeDisplay(order);
        
        // Status button
        const statusButton = getStatusButton(order);
        
        return `
            <tr data-order-id="${order.id}">
                <td>${productName}</td>
                <td>${countryFlag}</td>
                <td>${order.phone_number || 'N/A'}</td>
                <td class="countdown-timer ${order.sms_code ? 'completed' : ''}" data-expires="${order.expires_at}" data-has-code="${!!order.sms_code}">${ttlDisplay}</td>
                <td class="code-column">${codeDisplay}</td>
                <td class="status-column">${statusButton}</td>
            </tr>
        `;
    }).join('');
    
    // Start countdown timers
    startCountdownTimers();
}

// Get TTL display for countdown
function getTTLDisplay(expiresAt, order) {
    // If order has received SMS code, show checkmark
    if (order.sms_code) {
        return '✅';
    }
    
    if (!expiresAt) return '--:--';
    
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = expiry - now;
    
    if (diff <= 0) return 'EXPIRED';
    
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Get code display based on order status
function getCodeDisplay(order) {
    if (order.sms_code) {
        return `<strong>${order.sms_code}</strong>`;
    }
    
    if (order.status === 'PENDING' || order.status === 'RECEIVED') {
        return `<div class="loading-spinner"></div>`;
    }
    
    return '--';
}

// Get status button based on order status
function getStatusButton(order) {
    // Show "Success" only when SMS code is actually received
    if (order.sms_code) {
        return '<span class="status-success">Success</span>';
    }
    
    // Show cancel button for active orders (pending or received status but no SMS code yet)
    if (order.status === 'PENDING' || order.status === 'RECEIVED') {
        return `<button class="status-cancel" onclick="cancelOrder('${order.id}')">Cancel</button>`;
    }
    
    // For finished orders without SMS code (shouldn't happen but just in case)
    if (order.status === 'FINISHED') {
        return '<span class="status-success">Success</span>';
    }
    
    // All other statuses (expired, cancelled, timeout, etc.) should not appear in this table
    // since we filtered them out, but just in case:
    return '<span class="status-cancel">Completed</span>';
}

// Start countdown timers
function startCountdownTimers() {
    const timerElements = document.querySelectorAll('.countdown-timer[data-expires]');
    
    timerElements.forEach(element => {
        const expiresAt = element.dataset.expires;
        const hasCode = element.dataset.hasCode === 'true';
        
        if (!expiresAt || hasCode) return; // Don't start timer if SMS code received
        
        const updateTimer = () => {
            const now = new Date();
            const expiry = new Date(expiresAt);
            const diff = expiry - now;
            
            if (diff <= 0) {
                element.textContent = 'EXPIRED';
                element.style.color = '#dc3545';
                element.style.fontWeight = 'bold';
                clearInterval(element.interval);
                
                // Remove the expired order row from the table immediately
                const orderRow = element.closest('tr');
                if (orderRow) {
                    // Add a fade-out animation before removing
                    orderRow.style.transition = 'opacity 0.5s ease-out';
                    orderRow.style.opacity = '0.5';
                    
                    setTimeout(() => {
                        // Remove the row with a slide-up animation
                        orderRow.style.transition = 'all 0.3s ease-out';
                        orderRow.style.transform = 'translateY(-20px)';
                        orderRow.style.opacity = '0';
                        
                        setTimeout(() => {
                            orderRow.remove();
                            
                            // Check if table is now empty and show appropriate message
                            const tableBody = document.querySelector('#recentOrdersTable tbody');
                            if (tableBody && tableBody.children.length === 0) {
                                tableBody.innerHTML = `
                                    <tr>
                                        <td colspan="6" class="text-center text-muted py-4">
                                            <i class="fas fa-inbox fa-2x mb-3 d-block"></i>
                                            No active orders. Purchase a number to get started!
                                        </td>
                                    </tr>
                                `;
                            }
                        }, 300);
                    }, 500);
                }
                
                // Note: The daemon will still process the refund in the background
                console.log('Expired order removed from table - daemon will process refund');
            } else {
                const minutes = Math.floor(diff / 60000);
                const seconds = Math.floor((diff % 60000) / 1000);
                element.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        };
        
        // Clear any existing interval
        if (element.interval) {
            clearInterval(element.interval);
        }
        
        // Update immediately and then every second
        updateTimer();
        element.interval = setInterval(updateTimer, 1000);
    });
}

// Get status class for order status
function getStatusClass(status) {
    const statusClasses = {
        'PENDING': 'bg-warning',
        'RECEIVED': 'bg-primary', 
        'FINISHED': 'bg-success',
        'CANCELLED': 'bg-danger',
        'TIMEOUT': 'bg-secondary'
    };
    
    return statusClasses[status] || 'bg-secondary';
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

// Show success message
function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 5000);
    }
}

// Setup dropdown toggle functionality
function setupDropdownToggle(type) {
    const selected = document.getElementById(`${type}DropdownSelected`);
    const container = document.getElementById(`${type}DropdownContainer`);
    const search = document.getElementById(`${type}Search`);
    
    if (!selected || !container || !search) {
        console.error(`Missing elements for ${type} dropdown`);
        return;
    }
    
    // Toggle dropdown
    selected.addEventListener('click', (e) => {
        e.stopPropagation();
        
        // Close other dropdowns first
        ['country', 'service'].forEach(otherType => {
            if (otherType !== type) {
                const otherContainer = document.getElementById(`${otherType}DropdownContainer`);
                const otherSelected = document.getElementById(`${otherType}DropdownSelected`);
                if (otherContainer && otherSelected) {
                    otherContainer.classList.remove('open');
                    otherSelected.classList.remove('open');
                }
            }
        });
        
        // Toggle current dropdown
        const isOpen = container.classList.contains('open');
        
        if (isOpen) {
            container.classList.remove('open');
            selected.classList.remove('open');
            
            // Remove body class for service hiding
            if (type === 'country') {
                document.body.classList.remove('country-dropdown-open');
            }
        } else {
            container.classList.add('open');
            selected.classList.add('open');
            
            // Simple positioning - let CSS handle it
            container.style.position = 'absolute';
            container.style.top = '100%';
            container.style.left = '0';
            container.style.right = '0';
            container.style.zIndex = '10000';
            
            // Add body class to hide service elements when country is open
            if (type === 'country') {
                document.body.classList.add('country-dropdown-open');
            }
            
            // Focus search input when opened
            setTimeout(() => search.focus(), 100);
        }
    });
    
    // Search functionality
    search.addEventListener('input', (e) => {
        const searchTerm = e.target.value;
        const data = type === 'country' ? countries : services;
        populateCustomDropdown(type, data, searchTerm);
    });
    
    // Prevent search input clicks from closing dropdown
    search.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Prevent search input mousedown from interfering
    search.addEventListener('mousedown', (e) => {
        e.stopPropagation();
    });
    
    // Prevent container clicks from closing dropdown, but allow scrolling
    container.addEventListener('click', (e) => {
        // Only stop propagation if not clicking on scroll area
        if (e.target === container || e.target.closest('.dropdown-options')) {
            e.stopPropagation();
        }
    });
    
    container.addEventListener('mousedown', (e) => {
        // Only stop propagation if not scrolling
        if (e.target === container || e.target.closest('.dropdown-options')) {
            e.stopPropagation();
        }
    });
    
    // Prevent touch events from interfering with scrolling
    const optionsContainer = container.querySelector('.dropdown-options');
    if (optionsContainer) {
        optionsContainer.addEventListener('touchstart', (e) => {
            e.stopPropagation();
        });
        
        optionsContainer.addEventListener('touchmove', (e) => {
            e.stopPropagation();
        });
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
    ['country', 'service'].forEach(type => {
        const container = document.getElementById(`${type}DropdownContainer`);
        const selected = document.getElementById(`${type}DropdownSelected`);
        
        if (container && selected && !selected.contains(e.target) && !container.contains(e.target)) {
            container.classList.remove('open');
            selected.classList.remove('open');
            
            // Remove backdrop
            const backdrop = document.getElementById(`${type}-dropdown-backdrop`);
            if (backdrop) {
                backdrop.remove();
            }
            
            // Remove body class when dropdown closes
            if (type === 'country') {
                document.body.classList.remove('country-dropdown-open');
            }
            
            // Restore service elements when country dropdown closes
            if (type === 'country') {
                const serviceSelected = document.getElementById('serviceDropdownSelected');
                const serviceContainer = document.getElementById('serviceDropdownContainer');
                if (serviceSelected && serviceContainer) {
                    serviceSelected.style.display = '';
                    serviceContainer.style.display = '';
                }
            }
        }
    });
});

// Check SMS for order
async function checkSMS(orderId) {
    try {
        const response = await fetch(`/api/5sim/order/${orderId}/status/`);
        const data = await response.json();
        
        if (data.success) {
            if (data.sms && data.sms.length > 0) {
                const latestSMS = data.sms[data.sms.length - 1];
                showSuccess(`SMS received: ${latestSMS.text}`);
                
                // Immediately refresh orders to show success status and stop timer
                loadRecentOrders();
            } else {
                showSuccess('No new SMS messages yet. Keep checking!');
            }
        } else {
            showError(data.error || 'Failed to check SMS');
        }
    } catch (error) {
        console.error('Error checking SMS:', error);
        showError('Network error while checking SMS');
    }
}

// Cancel order
async function cancelOrder(orderId) {
    try {
        const response = await fetch(`/api/5sim/order/${orderId}/cancel/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Order cancelled successfully! Refund of ₦${data.refund_amount || 'amount'} has been credited to your account.`);
            
            // Update balance immediately
            if (data.new_balance !== undefined) {
                updateBalanceDisplay(data.new_balance);
            }
            
            // Refresh orders table immediately
            loadRecentOrders();
        } else {
            showError(data.error || 'Failed to cancel order');
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        showError('Network error while cancelling order');
    }
}

// Show order details (placeholder)
function showOrderDetails(orderId) {
    showSuccess(`Order details for ${orderId} - Feature coming soon!`);
}

// Check active orders for new SMS codes
async function checkActiveOrdersForSMS() {
    try {
        const tableBody = document.querySelector('#recentOrdersTable tbody');
        if (!tableBody) return;
        
        const orderRows = tableBody.querySelectorAll('tr[data-order-id]');
        
        for (const row of orderRows) {
            const orderId = row.dataset.orderId;
            const statusCell = row.querySelector('.status-column');
            const codeCell = row.querySelector('.code-column');
            
            // Only check orders that are PENDING and don't have codes yet
            if (statusCell && statusCell.textContent.includes('PENDING') && 
                codeCell && (codeCell.textContent.includes('Waiting') || codeCell.innerHTML.includes('spinner'))) {
                
                // Check this specific order for SMS updates
                await checkOrderSMSUpdate(orderId, codeCell);
            }
        }
    } catch (error) {
        console.error('Error checking active orders for SMS:', error);
    }
}

// Check specific order for SMS update
async function checkOrderSMSUpdate(orderId, codeCell) {
    try {
        const response = await fetch(`/api/5sim/order/${orderId}/status/`);
        const data = await response.json();
        
        if (data.success && data.sms_codes && data.sms_codes.length > 0) {
            // Update the code cell with the received SMS
            const latestSMS = data.sms_codes[data.sms_codes.length - 1];
            codeCell.innerHTML = `<span class="status-success">${latestSMS.text}</span>`;
            
            // Optional: Show a notification for new SMS
            showSuccess(`New SMS received for order ${orderId}: ${latestSMS.text}`);
            
            // Force a full refresh to update all data
            setTimeout(() => {
                loadRecentOrders();
            }, 1000);
        }
    } catch (error) {
        console.error(`Error checking SMS for order ${orderId}:`, error);
    }
}

// Helper functions for dropdown spacing on mobile
function addDropdownSpacing() {
    if (window.innerWidth <= 768) {
        // Find the form card (purchase card) - try multiple selectors
        let formCard = null;
        
        // Try to find by form-stack class
        const formStackElement = document.querySelector('.form-stack');
        if (formStackElement) {
            formCard = formStackElement.closest('.glass-card') || formStackElement.closest('.card');
        }
        
        // Fallback: find any card that contains the country dropdown
        if (!formCard) {
            const countryDropdown = document.getElementById('countryDropdownSelected');
            if (countryDropdown) {
                formCard = countryDropdown.closest('.glass-card') || countryDropdown.closest('.card');
            }
        }
        
        // Fallback: find the first glass-card
        if (!formCard) {
            formCard = document.querySelector('.glass-card');
        }
        
        if (formCard) {
            formCard.classList.add('dropdown-space');
            console.log('Added dropdown spacing to card');
        }
    }
}

function removeDropdownSpacing() {
    // Remove spacing from all cards
    const allCards = document.querySelectorAll('.glass-card');
    allCards.forEach(card => {
        card.classList.remove('dropdown-space');
    });
    
    // Remove form group classes
    document.querySelectorAll('.form-group').forEach(group => {
        group.classList.remove('country-open', 'service-open');
    });
}

// Handle window resize to close dropdowns and remove spacing
window.addEventListener('resize', () => {
    const countryContainer = document.getElementById('countryDropdownContainer');
    const serviceContainer = document.getElementById('serviceDropdownContainer');
    
    // Close dropdowns and remove spacing on resize
    [countryContainer, serviceContainer].forEach(container => {
        if (container) {
            container.style.display = 'none';
        }
    });
    
    removeDropdownSpacing();
});

// Close dropdowns when clicking outside and remove spacing
document.addEventListener('click', (e) => {
    const countryContainer = document.getElementById('countryDropdownContainer');
    const serviceContainer = document.getElementById('serviceDropdownContainer');
    const countrySelected = document.getElementById('countryDropdownSelected');
    const serviceSelected = document.getElementById('serviceDropdownSelected');
    
    let dropdownClosed = false;
    
    // Check if click is outside dropdowns
    if (!countrySelected?.contains(e.target) && !countryContainer?.contains(e.target)) {
        if (countryContainer && countryContainer.style.display === 'block') {
            countryContainer.style.display = 'none';
            dropdownClosed = true;
        }
    }
    
    if (!serviceSelected?.contains(e.target) && !serviceContainer?.contains(e.target)) {
        if (serviceContainer && serviceContainer.style.display === 'block') {
            serviceContainer.style.display = 'none';
            dropdownClosed = true;
        }
    }
    
    // Remove spacing if any dropdown was closed
    if (dropdownClosed) {
        removeDropdownSpacing();
    }
});

// Cleanup expired orders that might have been missed
function cleanupExpiredOrders() {
    try {
        const tableBody = document.querySelector('#recentOrdersTable tbody');
        if (!tableBody) return;
        
        const orderRows = tableBody.querySelectorAll('tr[data-order-id]');
        let removedCount = 0;
        
        orderRows.forEach(row => {
            const countdownElement = row.querySelector('.countdown-timer[data-expires]');
            if (!countdownElement) return;
            
            const expiresAt = countdownElement.dataset.expires;
            const hasCode = countdownElement.dataset.hasCode === 'true';
            
            if (!expiresAt || hasCode) return;
            
            const now = new Date();
            const expiry = new Date(expiresAt);
            const diff = expiry - now;
            
            // If order has expired, remove it
            if (diff <= 0) {
                console.log('Cleaning up expired order row');
                row.style.transition = 'all 0.3s ease-out';
                row.style.transform = 'translateY(-20px)';
                row.style.opacity = '0';
                
                setTimeout(() => {
                    row.remove();
                    removedCount++;
                    
                    // Check if table is now empty after cleanup
                    const remainingRows = tableBody.querySelectorAll('tr[data-order-id]');
                    if (remainingRows.length === 0) {
                        tableBody.innerHTML = `
                            <tr>
                                <td colspan="6" class="text-center text-muted py-4">
                                    <i class="fas fa-inbox fa-2x mb-3 d-block"></i>
                                    No active orders. Purchase a number to get started!
                                </td>
                            </tr>
                        `;
                    }
                }, 300);
            }
        });
        
        if (removedCount > 0) {
            console.log(`Cleaned up ${removedCount} expired orders`);
        }
    } catch (error) {
        console.error('Error cleaning up expired orders:', error);
    }
}

// Initialize everything when page loads
async function initialize() {
    console.log('Initializing dashboard...');
    
    await loadCountries();
    await loadServices();
    
    // Setup dropdown functionality
    setupDropdownToggle('country');
    setupDropdownToggle('service');
    
    // Load recent orders
    loadRecentOrders();
    
    // Auto-refresh orders every 15 seconds to update TTL and check for new SMS codes
    setInterval(() => {
        loadRecentOrders();
    }, 15000);
    
    // Dedicated SMS code checker - runs every 10 seconds for active orders
    setInterval(() => {
        checkActiveOrdersForSMS();
    }, 10000);
    
    // Cleanup expired orders - runs every 30 seconds to catch any missed expirations
    setInterval(() => {
        cleanupExpiredOrders();
    }, 30000);
    
    console.log('Dashboard initialization complete');
}

// Start initialization when DOM is ready
document.addEventListener('DOMContentLoaded', initialize);