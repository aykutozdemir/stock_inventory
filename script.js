// Automatically detect the API URL
const API_URL = `${window.location.protocol}//${window.location.host}/api`;

let currentView = 'stocks';
let editingCategoryId = null;
let editingStockId = null;
let categoryViewMode = 'cards'; // 'cards' or 'table'
let stockViewMode = 'cards'; // 'cards' or 'table'
let confirmCallback = null; // For confirmation modal
let renameCallback = null; // For rename modal
let renameConversationId = null; // Current conversation being renamed

// Navigation
document.getElementById('btnCategories').addEventListener('click', () => showView('categories'));
document.getElementById('btnStocks').addEventListener('click', () => showView('stocks'));
document.getElementById('btnAI').addEventListener('click', () => showView('ai'));

function showView(view) {
    currentView = view;
    
    // Update navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    if (view === 'categories') {
        document.getElementById('btnCategories').classList.add('active');
    } else if (view === 'ai') {
        document.getElementById('btnAI').classList.add('active');
    } else {
        document.getElementById('btnStocks').classList.add('active');
    }
    
    // Update views
    document.getElementById('categoriesView').classList.toggle('active', view === 'categories');
    document.getElementById('stocksView').classList.toggle('active', view === 'stocks');
    document.getElementById('aiView').classList.toggle('active', view === 'ai');
    
    // Load data for current view
    if (view === 'categories') {
        loadCategories();
    } else {
        loadStocks();
    }
}

// View Mode Toggle
function toggleViewMode(view, mode) {
    if (view === 'categories') {
        categoryViewMode = mode;
    } else if (view === 'stocks') {
        stockViewMode = mode;
    }
    
    // Update button states
    const viewName = view === 'categories' ? 'categoriesView' : 'stocksView';
    document.querySelectorAll(`#${viewName} .view-toggle-btn`).forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === mode) {
            btn.classList.add('active');
        }
    });
    
    // Reload data
    if (view === 'categories') {
        loadCategories();
    } else {
        displayStocks();
    }
}

// Categories
async function loadCategories() {
    try {
        const response = await fetch(`${API_URL}/categories`);
        const result = await response.json();
        
        const container = document.getElementById('categoriesList');
        if (result.data.length === 0) {
            container.innerHTML = '<div class="empty-state"><h3>No categories yet</h3><p>Add your first category to get started!</p></div>';
            container.classList.remove('table-view');
            return;
        }
        
        if (categoryViewMode === 'table') {
            container.classList.add('table-view');
            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Description</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${result.data.map(category => `
                            <tr>
                                <td>${escapeHtml(category.name)}</td>
                                <td>${escapeHtml(category.description || '-')}</td>
                                <td>
                                    <button class="btn btn-edit" onclick="editCategory(${category.id})" style="margin-right:0.5rem;">✏️</button>
                                    <button class="btn btn-danger" onclick="deleteCategory(${category.id})">❌</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            container.classList.remove('table-view');
            container.innerHTML = result.data.map(category => `
                <div class="card">
                    <div class="card-header">
                        <h3>${escapeHtml(category.name)}</h3>
                        <div class="card-actions">
                            <button class="btn btn-edit" onclick="editCategory(${category.id})">✏️</button>
                            <button class="btn btn-danger" onclick="deleteCategory(${category.id})">❌</button>
                        </div>
                    </div>
                    ${category.description ? `<div class="card-body">${escapeHtml(category.description)}</div>` : ''}
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading categories:', error);
        alert('Failed to load categories');
    }
}

function openCategoryModal(category = null) {
    editingCategoryId = category ? category.id : null;
    document.getElementById('categoryModalTitle').textContent = '📦 Electronic Components Inventory';
    document.getElementById('categoryId').value = category?.id || '';
    document.getElementById('categoryName').value = category?.name || '';
    document.getElementById('categoryDescription').value = category?.description || '';
    document.getElementById('categoryModal').classList.add('active');
    
    // Focus on name field
    setTimeout(() => {
        document.getElementById('categoryName').focus();
    }, 100);
}

function closeCategoryModal() {
    document.getElementById('categoryModal').classList.remove('active');
    document.getElementById('categoryForm').reset();
    editingCategoryId = null;
}

document.getElementById('categoryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('categoryName').value,
        description: document.getElementById('categoryDescription').value
    };
    
    try {
        const url = editingCategoryId 
            ? `${API_URL}/categories/${editingCategoryId}`
            : `${API_URL}/categories`;
        const method = editingCategoryId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeCategoryModal();
            loadCategories();
        } else {
            alert(result.message || 'Failed to save category');
        }
    } catch (error) {
        console.error('Error saving category:', error);
        alert('Failed to save category');
    }
});

async function editCategory(id) {
    const response = await fetch(`${API_URL}/categories`);
    const result = await response.json();
    const category = result.data.find(c => c.id === id);
    if (category) {
        openCategoryModal(category);
    }
}

async function deleteCategory(id) {
    openConfirmModal('Are you sure you want to delete this category?', async () => {
    
    try {
        const response = await fetch(`${API_URL}/categories/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            loadCategories();
        } else {
            alert(result.message || 'Failed to delete category');
        }
    } catch (error) {
        console.error('Error deleting category:', error);
        alert('Failed to delete category');
    }
    });
}

// Stocks
async function loadCategoriesForSelect() {
    try {
        const response = await fetch(`${API_URL}/categories`);
        const result = await response.json();
        const select = document.getElementById('stockCategory');
        const filter = document.getElementById('categoryFilter');
        
        const options = result.data.map(cat => 
            `<option value="${cat.id}">${escapeHtml(cat.name)}</option>`
        ).join('');
        
        select.innerHTML = '<option value="">Select Category</option>' + options;
        filter.innerHTML = '<option value="">All Categories</option>' + options;
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Store all stocks for search/filter
let allStocks = [];
let currentConversationId = null;
let messageSeq = 0; // ensures unique message element ids

async function loadStocks() {
    try {
        await loadCategoriesForSelect();
        
        // Load all stocks from API
        const response = await fetch(`${API_URL}/stocks`);
        const result = await response.json();
        allStocks = result.data;
        
        // Display with current filters
        displayStocks();
    } catch (error) {
        console.error('Error loading stocks:', error);
        alert('Failed to load stocks');
    }
}

function displayStocks() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
    const categoryId = document.getElementById('categoryFilter').value;
    const statusFilter = document.getElementById('stockStatusFilter').value;
    
    // Filter stocks based on search, category, and status
    let filteredStocks = allStocks.filter(stock => {
        // Category filter
        if (categoryId && stock.category_id != categoryId) {
            return false;
        }
        
        // Status filter
        if (statusFilter === 'zero' && stock.quantity !== 0) {
            return false;
        }
        if (statusFilter === 'critical' && (stock.quantity === 0 || stock.quantity > 5)) {
            return false;
        }
        
        // Search filter
        if (searchQuery) {
            const searchableText = `${stock.name} ${stock.description || ''} ${stock.location || ''} ${stock.category_name || ''}`.toLowerCase();
            return searchableText.includes(searchQuery);
        }
        
        return true;
    });
    
    const container = document.getElementById('stocksList');
    if (filteredStocks.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No items found</h3><p>Try adjusting your search or filters</p></div>';
        container.classList.remove('table-view');
        return;
    }
    
    if (stockViewMode === 'table') {
        container.classList.add('table-view');
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Quantity</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${filteredStocks.map(stock => {
                        let statusText = '';
                        let statusStyle = '';
                        if (stock.quantity === 0) {
                            statusText = '🔴 Out';
                            statusStyle = 'color: #ef4444;';
                        } else if (stock.quantity <= 5) {
                            statusText = '⚠️ Critical';
                            statusStyle = 'color: #f59e0b;';
                        } else {
                            statusText = '✓ OK';
                            statusStyle = 'color: #10b981;';
                        }
                        return `
                            <tr>
                                <td><strong>${escapeHtml(stock.name)}</strong></td>
                                <td>${escapeHtml(stock.category_name)}</td>
                                <td>${stock.quantity} ${escapeHtml(stock.unit || 'pcs')}</td>
                                <td>${escapeHtml(stock.location || '-')}</td>
                                <td style="${statusStyle} font-weight: 600;">${statusText}</td>
                                <td style="white-space: nowrap;">
                                    <button class="btn btn-edit" onclick="editStock(${stock.id})" style="margin-right:0.5rem;">✏️</button>
                                    <button class="btn btn-danger" onclick="deleteStock(${stock.id})" style="margin-right:0.5rem;">❌</button>
                                    <button class="btn btn-primary" onclick="useStockData(${stock.id}, ${stock.quantity})" ${stock.quantity === 0 ? 'disabled style="background: #ccc; cursor: not-allowed;"' : ''}>➖ Use</button>
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
    } else {
        container.classList.remove('table-view');
        container.innerHTML = filteredStocks.map(stock => {
            // Determine stock status
            let statusBadge = '';
            let statusColor = '';
            if (stock.quantity === 0) {
                statusBadge = '<div class="badge" style="background: #ef4444;">🔴 Out of Stock</div>';
            } else if (stock.quantity <= 5) {
                statusBadge = '<div class="badge" style="background: #f59e0b;">⚠️ Critical Stock</div>';
            }
            
            return `
            <div class="card">
                ${stock.image_path ? `<img src="${stock.image_path}" alt="${escapeHtml(stock.name)}" class="stock-image">` : ''}
                <div class="card-header">
                    <h3>${escapeHtml(stock.name)}</h3>
                    <div class="card-actions">
                        <button class="btn btn-edit" onclick="editStock(${stock.id})">✏️</button>
                        <button class="btn btn-danger" onclick="deleteStock(${stock.id})">❌</button>
                    </div>
                </div>
                <div class="card-body">
                    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap;">
                        <div class="badge">${escapeHtml(stock.category_name)}</div>
                        ${statusBadge}
                    </div>
                    <p style="margin: 0.5rem 0;">
                        <strong>Quantity:</strong> ${stock.quantity} ${escapeHtml(stock.unit || 'pcs')}
                    </p>
                    ${stock.location ? `<p style="margin: 0.5rem 0;"><strong>Location:</strong> ${escapeHtml(stock.location)}</p>` : ''}
                    ${stock.description ? `<p style="margin: 0.5rem 0;">${escapeHtml(stock.description)}</p>` : ''}
                </div>
                <div class="card-footer">
                    <button class="btn btn-primary" onclick="useStockData(${stock.id}, ${stock.quantity})" style="width: 100%;" ${stock.quantity === 0 ? 'disabled style="background: #ccc; cursor: not-allowed; width: 100%;"' : ''}>
                        ${stock.quantity === 0 ? '❌ Out of Stock' : '➖ Use Item'}
                    </button>
                </div>
            </div>
            `;
        }).join('');
    }
}

document.getElementById('categoryFilter').addEventListener('change', displayStocks);
document.getElementById('stockStatusFilter').addEventListener('change', displayStocks);
document.getElementById('searchInput').addEventListener('input', displayStocks);

function openStockModal(stock = null, quickAdd = false) {
    editingStockId = stock ? stock.id : null;
    document.getElementById('stockModalTitle').textContent = '📦 Electronic Components Inventory';
    
    // Pre-fill with common values for quick add
    const savedUnit = localStorage.getItem('lastUnit') || 'pcs';
    const savedLocation = localStorage.getItem('lastLocation') || '';
    
    document.getElementById('stockId').value = stock?.id || '';
    document.getElementById('stockName').value = stock?.name || '';
    document.getElementById('stockQuantity').value = stock?.quantity || (quickAdd ? 1 : 0);
    document.getElementById('stockUnit').value = stock?.unit || savedUnit;
    document.getElementById('stockLocation').value = stock?.location || (quickAdd ? 'Office' : savedLocation);
    document.getElementById('stockDescription').value = stock?.description || '';
    
    // Load categories for select
    loadCategoriesForSelect().then(() => {
        if (stock) {
            document.getElementById('stockCategory').value = stock.category_id;
        } else if (quickAdd) {
            // Auto-select first category for quick add
            const select = document.getElementById('stockCategory');
            if (select.options.length > 1) {
                select.selectedIndex = 1;
            }
        }
        
        // Show image preview if exists
        const preview = document.getElementById('stockImagePreview');
        if (stock && stock.image_path) {
            preview.innerHTML = `<div class="image-preview"><img src="${stock.image_path}" alt="Preview"></div>`;
        } else {
            preview.innerHTML = '';
        }
        
        document.getElementById('stockModal').classList.add('active');
        
        // Auto-focus on name field for faster input
        setTimeout(() => {
            document.getElementById('stockName').focus();
        }, 150);
    });
}

function closeStockModal() {
    document.getElementById('stockModal').classList.remove('active');
    
    // Save last used values for next time (but not for editing existing items)
    if (!editingStockId) {
        const lastUnit = document.getElementById('stockUnit').value;
        const lastLocation = document.getElementById('stockLocation').value;
        localStorage.setItem('lastUnit', lastUnit);
        localStorage.setItem('lastLocation', lastLocation);
    }
    
    document.getElementById('stockForm').reset();
    document.getElementById('stockImagePreview').innerHTML = '';
    editingStockId = null;
}

document.getElementById('stockForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    
    const data = {
        name: document.getElementById('stockName').value,
        category_id: parseInt(document.getElementById('stockCategory').value),
        quantity: parseInt(document.getElementById('stockQuantity').value),
        unit: document.getElementById('stockUnit').value,
        location: document.getElementById('stockLocation').value,
        description: document.getElementById('stockDescription').value
    };
    
    try {
        // Update or create stock first
        const url = editingStockId 
            ? `${API_URL}/stocks/${editingStockId}`
            : `${API_URL}/stocks`;
        const method = editingStockId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!result.success) {
            alert(result.message || 'Failed to save stock');
            return;
        }
        
        // Upload image if selected (check both inputs)
        const imageInput = document.getElementById('stockImage');
        const imageInputCamera = document.getElementById('stockImageCamera');
        const imageFile = imageInput.files[0] || imageInputCamera.files[0];
        
        if (imageFile) {
            const stockId = editingStockId || result.data.id;
            const imgFormData = new FormData();
            imgFormData.append('file', imageFile);
            
            const imgResponse = await fetch(`${API_URL}/stocks/${stockId}/image`, {
                method: 'POST',
                body: imgFormData
            });
            
            const imgResult = await imgResponse.json();
            if (!imgResult.success) {
                console.error('Failed to upload image:', imgResult.message);
            }
        }
        
        closeStockModal();
        loadStocks();
    } catch (error) {
        console.error('Error saving stock:', error);
        alert('Failed to save stock');
    }
});

async function editStock(id) {
    try {
        const response = await fetch(`${API_URL}/stocks/${id}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            // Also fetch category name
            const categories = await (await fetch(`${API_URL}/categories`)).json();
            const category = categories.data.find(c => c.id === result.data.category_id);
            result.data.category_name = category ? category.name : '';
            
            openStockModal(result.data);
        } else {
            alert('Stock not found');
        }
    } catch (error) {
        console.error('Error loading stock:', error);
        alert('Failed to load stock details');
    }
}

async function deleteStock(id) {
    openConfirmModal('Are you sure you want to delete this stock item?', async () => {
    
    try {
        const response = await fetch(`${API_URL}/stocks/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            loadStocks();
        } else {
            alert(result.message || 'Failed to delete stock');
        }
    } catch (error) {
        console.error('Error deleting stock:', error);
        alert('Failed to delete stock');
    }
    });
}

// Usage tracking
let currentUsageStockId = null;
let currentUsageStockName = '';
let currentUsageStockQuantity = 0;

async function useStockData(id, currentQty) {
    try {
        const response = await fetch(`${API_URL}/stocks/${id}`);
        const result = await response.json();
        
        if (!result.success) {
            alert('Failed to load stock details');
            return;
        }
        
        const stock = result.data;
        useStock(id, stock.name, currentQty);
    } catch (error) {
        console.error('Error loading stock:', error);
        alert('Failed to load stock details');
    }
}

function useStock(id, name, currentQty) {
    currentUsageStockId = id;
    currentUsageStockName = name;
    currentUsageStockQuantity = currentQty;
    
    document.getElementById('usageModalText').textContent = `Using: ${name} (Available: ${currentQty})`;
    
    // Set max to prevent using more than available
    const usageInput = document.getElementById('usageQuantity');
    usageInput.max = currentQty;
    usageInput.value = '1';
    
    document.getElementById('usageModal').classList.add('active');
    
    // Focus on input after modal opens
    setTimeout(() => {
        document.getElementById('usageQuantity').focus();
    }, 100);
}

function closeUsageModal() {
    document.getElementById('usageModal').classList.remove('active');
    document.getElementById('usageForm').reset();
    currentUsageStockId = null;
}

document.getElementById('usageForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const usedQty = parseInt(document.getElementById('usageQuantity').value);
    
    if (usedQty > currentUsageStockQuantity) {
        alert(`You can't use more than available (${currentUsageStockQuantity})!`);
        return;
    }
    
    if (usedQty <= 0) {
        alert('Please enter a valid quantity');
        return;
    }
    
    try {
        // Get current stock details
        const response = await fetch(`${API_URL}/stocks/${currentUsageStockId}`);
        const result = await response.json();
        
        if (!result.success) {
            alert('Failed to load stock details');
            return;
        }
        
        const stock = result.data;
        const newQuantity = stock.quantity - usedQty;
        
        // Update stock with new quantity
        const updateData = {
            name: stock.name,
            category_id: stock.category_id,
            quantity: newQuantity,
            unit: stock.unit,
            location: stock.location,
            description: stock.description
        };
        
        const updateResponse = await fetch(`${API_URL}/stocks/${currentUsageStockId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        const updateResult = await updateResponse.json();
        
        if (updateResult.success) {
            closeUsageModal();
            loadStocks();
        } else {
            alert(updateResult.message || 'Failed to update stock');
        }
    } catch (error) {
        console.error('Error using stock:', error);
        alert('Failed to update stock');
    }
});

// Image preview
// Handle image preview for both file inputs
function handleImagePreview(input) {
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        const preview = document.getElementById('stockImagePreview');
        
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `<div class="image-preview"><img src="${e.target.result}" alt="Preview"></div>`;
            };
            reader.readAsDataURL(file);
        } else {
            preview.innerHTML = '';
        }
    });
}

handleImagePreview(document.getElementById('stockImage'));
handleImagePreview(document.getElementById('stockImageCamera'));

// Utility function
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// AI Chat Functions
async function askAI() {
    const input = document.getElementById('aiInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Clear input
    input.value = '';
    
    // Add user message
    addChatMessage('user', question);
    
    // Show thinking indicator
    const thinkingId = addChatMessage('assistant', '🤔 Thinking...');
    
    try {
        // Always route via backend API using LangChain local LLM
        const response = await fetch(`${API_URL}/ai/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question,
                conversation_id: currentConversationId 
            })
        });
        const result = await response.json();
        
        // Remove thinking message
        removeChatMessage(thinkingId);
        
        if (result.success) {
            if (result.data && result.data.conversation_id) {
                currentConversationId = result.data.conversation_id;
            }
            let assistantText = result.data.answer || '';
            if (result.data && result.data.model) {
                assistantText += `\n\n🧠 Model: ${result.data.model}`;
            }
            if (Array.isArray(result.data?.inventory) && result.data.inventory.length > 0) {
                addChatTable('assistant', result.data.inventory);
                if (assistantText) addChatMessage('assistant', assistantText);
            } else {
                addChatMessage('assistant', assistantText);
            }
        } else {
            addChatMessage('assistant', '❌ ' + result.message);
        }
    } catch (error) {
        removeChatMessage(thinkingId);
        addChatMessage('assistant', '❌ Error: Could not connect to AI service');
        console.error('Error:', error);
    }
}

function addChatMessage(role, message) {
    const container = document.getElementById('aiChatMessages');
    const msgId = 'msg_' + (++messageSeq);
    
    const msgDiv = document.createElement('div');
    msgDiv.id = msgId;
    msgDiv.style.cssText = `
        margin-bottom: 1rem;
        padding: 0.75rem;
        border-radius: 8px;
        background: ${role === 'user' ? '#2563eb' : '#e2e8f0'};
        color: ${role === 'user' ? 'white' : '#1e293b'};
        max-width: 80%;
        margin-left: ${role === 'user' ? 'auto' : '0'};
        margin-right: ${role === 'user' ? '0' : 'auto'};
        word-wrap: break-word;
        white-space: pre-wrap;
    `;
    msgDiv.textContent = message;
    
    // If it's the first non-welcome message, clear welcome
    if (container.children.length > 0 && container.children[0].textContent.includes('👋')) {
        container.innerHTML = '';
    }
    
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    
    return msgId;
}

function addChatTable(role, rows) {
    const container = document.getElementById('aiChatMessages');
    const msgId = 'msg_' + (++messageSeq);
    const msgDiv = document.createElement('div');
    msgDiv.id = msgId;
    msgDiv.style.cssText = `
        margin-bottom: 1rem;
        padding: 0.75rem;
        border-radius: 8px;
        background: ${role === 'user' ? '#2563eb' : '#e2e8f0'};
        color: ${role === 'user' ? 'white' : '#1e293b'};
        max-width: 100%;
        margin-left: ${role === 'user' ? 'auto' : '0'};
        margin-right: ${role === 'user' ? '0' : 'auto'};
        overflow-x: auto;
    `;
    // Group rows by category and render a titled table per category
    const groups = rows.reduce((acc, r) => {
        const cat = (r.category || 'Other').toString();
        (acc[cat] ||= []).push(r);
        return acc;
    }, {});
    const headers = ['name','quantity','unit'];
    const th = (h) => `<th style=\"text-align:left;padding:6px 8px;border-bottom:1px solid #cbd5e1;\">${h.toUpperCase()}</th>`;
    const td = (v) => `<td style=\"padding:6px 8px;border-bottom:1px solid #e2e8f0;\">${escapeHtml(String(v ?? ''))}</td>`;
    let html = '';
    Object.keys(groups).sort().forEach(cat => {
        const items = groups[cat];
        html += `
            <div style=\"font-weight:600;margin:4px 0 6px;\">${escapeHtml(cat)}</div>
            <table style=\"border-collapse:collapse;width:100%;font-size:0.95rem;margin-bottom:10px;\">
                <thead><tr>${headers.map(th).join('')}</tr></thead>
                <tbody>
                    ${items.map(r => `<tr>${td(r.name)}${td(r.quantity)}${td(r.unit)}</tr>`).join('')}
                </tbody>
            </table>
        `;
    });
    msgDiv.innerHTML = html;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    return msgId;
}

function removeChatMessage(msgId) {
    const msg = document.getElementById(msgId);
    if (msg) {
        msg.remove();
    }
}

// Conversation Management
async function loadConversations() {
    try {
        const response = await fetch(`${API_URL}/conversations`);
        const result = await response.json();
        
        if (!result.success) {
            console.error('Failed to load conversations');
            return;
        }
        
        const container = document.getElementById('conversationsList');
        if (result.data.length === 0) {
            container.innerHTML = '<div style="color: #64748b; font-size: 0.9rem; text-align: center; padding: 1rem;">No conversations yet</div>';
            return;
        }
        
        container.innerHTML = result.data.map(conv => 
            `<div onclick="loadConversation(${conv.id})" style="padding:0.75rem;margin-bottom:0.5rem;border-radius:8px;cursor:pointer;background:${currentConversationId === conv.id ? '#e0e7ff' : '#f8fafc'};border:${currentConversationId === conv.id ? '2px solid #2563eb' : '1px solid transparent'};">     
                <div style="font-weight:500;">${escapeHtml(conv.title)}</div>
                <div style="display:flex;justify-content:space-between;margin-top:0.5rem;align-items:center;">                                                  
                    <span style="font-size:0.75rem;color:#64748b;">${conv.message_count || 0} messages</span>                                                   
                    <div>
                        <button onclick="event.stopPropagation();renameConversation(${conv.id},'${escapeHtml(conv.title).replace(/'/g, "\\'")}')" class="btn btn-edit" style="margin-right:0.5rem;">✏️</button>
                        <button onclick="event.stopPropagation();deleteConversation(${conv.id})" class="btn btn-danger">❌</button>
                    </div>
                </div>
            </div>`
        ).join('');
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

async function createConversation() {
    try {
        const response = await fetch(`${API_URL}/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Conversation' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            await loadConversations();
            await loadConversation(result.data.id);
        } else {
            alert('Failed to create conversation');
        }
    } catch (error) {
        console.error('Error creating conversation:', error);
        alert('Failed to create conversation');
    }
}

async function loadConversation(id) {
    try {
        currentConversationId = id;
        
        // Load messages
        const response = await fetch(`${API_URL}/conversations/${id}/messages`);
        const result = await response.json();
        
        if (!result.success) {
            alert('Failed to load conversation');
            return;
        }
        
        // Display messages
        const container = document.getElementById('aiChatMessages');
        container.innerHTML = '';
        
        result.data.forEach(msg => {
            addChatMessage(msg.role, msg.message);
        });
        
        // Update conversation list to highlight active one
        await loadConversations();
    } catch (error) {
        console.error('Error loading conversation:', error);
        alert('Failed to load conversation');
    }
}

async function deleteConversation(id) {
    openConfirmModal('Delete this conversation?', async () => {
    
    try {
        const response = await fetch(`${API_URL}/conversations/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            if (currentConversationId === id) {
                currentConversationId = null;
                document.getElementById('aiChatMessages').innerHTML = '<div style="text-align: center; color: #64748b; padding: 2rem;"><p>👋 Hi! I\'m your AI assistant. Ask me about your inventory!</p><p style="font-size:0.9rem;margin-top:0.5rem;">Select a conversation or start a new one.</p></div>';
            }
            await loadConversations();
        } else {
            alert('Failed to delete conversation');
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
        alert('Failed to delete conversation');
    }
    });
}

function openRenameModal(id, currentTitle) {
    renameConversationId = id;
    document.getElementById('renameInput').value = currentTitle;
    document.getElementById('renameModal').classList.add('active');
    document.getElementById('renameInput').focus();
    document.getElementById('renameInput').select();
}

function closeRenameModal() {
    document.getElementById('renameModal').classList.remove('active');
    renameConversationId = null;
}

function renameConversation(id, currentTitle) {
    renameConversationId = id;
    openRenameModal(id, currentTitle);
}

// Override showView to load conversations when AI tab is active
window.showView = (function() {
    const originalShowView = showView;
    return function(view) {
        originalShowView(view);
        if (view === 'ai') loadConversations();
    };
})();

// Confirmation Modal Functions
function openConfirmModal(message, onConfirm) {
    document.getElementById('confirmModalText').textContent = message;
    confirmCallback = onConfirm;
    document.getElementById('confirmModal').classList.add('active');
    
    // Focus on confirm button
    setTimeout(() => {
        document.getElementById('confirmOkBtn').focus();
    }, 100);
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.remove('active');
    confirmCallback = null;
}

// Setup confirm modal OK button
document.getElementById('confirmOkBtn').addEventListener('click', () => {
    if (confirmCallback) {
        confirmCallback();
        closeConfirmModal();
    }
});

// Setup rename form submit
document.getElementById('renameForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const newTitle = document.getElementById('renameInput').value.trim();
    if (!newTitle || !renameConversationId) return;
    
    try {
        const response = await fetch(`${API_URL}/conversations/${renameConversationId}/title`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeRenameModal();
            await loadConversations();
        } else {
            alert('Failed to rename conversation');
        }
    } catch (error) {
        console.error('Error renaming conversation:', error);
        alert('Failed to rename conversation');
    }
});

// Alert Modal Functions
function showAlert(message) {
    document.getElementById('alertModalText').textContent = message;
    document.getElementById('alertModal').classList.add('active');
    
    // Focus on OK button
    setTimeout(() => {
        document.getElementById('alertOkBtn').focus();
    }, 100);
}

function closeAlertModal() {
    document.getElementById('alertModal').classList.remove('active');
}

// Setup alert modal OK button (Enter key)
document.getElementById('alertOkBtn').addEventListener('click', () => {
    closeAlertModal();
});

// Override alert function to use modal
window.alert = showAlert;

// ESC key to close modals
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // Close any open modal
        const modals = document.querySelectorAll('.modal.active');
        modals.forEach(modal => {
            modal.classList.remove('active');
        });
        
        // Reset states
        editingCategoryId = null;
        editingStockId = null;
        currentUsageStockId = null;
        renameConversationId = null;
    }
});

// Initialize
loadStocks();
