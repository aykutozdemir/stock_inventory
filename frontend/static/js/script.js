// Automatically detect the API URL
const API_URL = `${window.location.protocol}//${window.location.host}/api`;

// Detect if we're in a webview environment
const isWebView = (() => {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    return /webview|wv|pywebview/i.test(userAgent) ||
           /QtWebEngine/i.test(userAgent) ||
           /Electron/i.test(userAgent) ||
           window.pywebview !== undefined;
})();

console.log('Environment detection:', { isWebView, userAgent: navigator.userAgent });

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
                            <th>Created At</th>
                            <th>Updated At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${result.data.map(category => `
                            <tr>
                                <td>${escapeHtml(category.name)}</td>
                                <td>${escapeHtml(category.description || '-')}</td>
                                <td>${new Date(category.created_at).toLocaleString()}</td>
                                <td>${new Date(category.updated_at).toLocaleString()}</td>
                                <td>
                                    <button class="btn btn-edit" onclick="editCategory(${category.id})" style="margin-right:0.5rem;">✏️</button>
                                    <button class="btn btn-danger" onclick="deleteCategory(${category.id}, '${escapeHtml(category.name)}')">❌</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            container.classList.remove('table-view');
            container.innerHTML = result.data.map(category => `
                <div class="card" onclick="showCategoryDetails(${category.id})" style="cursor: pointer;">
                    <div class="card-header">
                        <h3>${escapeHtml(category.name)}</h3>
                        <div class="card-actions">
                            <button class="btn btn-edit" onclick="event.stopPropagation(); editCategory(${category.id})">✏️</button>
                            <button class="btn btn-danger" onclick="event.stopPropagation(); deleteCategory(${category.id}, '${escapeHtml(category.name)}')">❌</button>
                        </div>
                    </div>
                    ${category.description ? `<div class="card-body">${escapeHtml(category.description)}</div>` : ''}
                    <div class="card-footer" style="font-size: 0.9em; color: #666; padding: 0.5rem;">
                        ${category.stock_count || 0} item${(category.stock_count || 0) !== 1 ? 's' : ''}
                    </div>
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
    document.getElementById('categoryModalTitle').textContent = editingCategoryId ? 'Edit Category' : 'Add Category';
    document.getElementById('categoryId').value = category?.id || '';
    document.getElementById('categoryName').value = category?.name || '';
    document.getElementById('categoryDescription').value = category?.description || '';
    const categoryModal = document.getElementById('categoryModal');
    categoryModal.classList.add('active');
    categoryModal.style.display = 'flex'; // Force display for webview compatibility
    categoryModal.style.position = 'fixed'; // Ensure positioning
    categoryModal.style.top = '0';
    categoryModal.style.left = '0';
    categoryModal.style.width = '100%';
    categoryModal.style.height = '100%';
    categoryModal.style.zIndex = '999999';
    categoryModal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';

    // Force the modal content to be visible
    const modalContent = categoryModal.querySelector('.modal-content');
    if (modalContent) {
        modalContent.style.position = 'relative';
        modalContent.style.zIndex = '1000000';
        modalContent.style.display = 'block';
        modalContent.style.visibility = 'visible';
    }
    
    // Focus on name field
    setTimeout(() => {
        document.getElementById('categoryName').focus();
    }, 100);
}

function closeCategoryModal() {
    const modal = document.getElementById('categoryModal');
    modal.classList.remove('active');
    modal.style.display = 'none'; // Force hide for webview compatibility
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

async function deleteCategory(id, name) {
    const message = `Are you sure you want to delete the category "${name}"? This action cannot be undone.`;
    openConfirmModal(message, async () => {
    
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

// Store all components for search/filter
let allStocks = [];
let currentConversationId = null;
let messageSeq = 0; // ensures unique message element ids

async function loadStocks() {
    try {
        await loadCategoriesForSelect();
        
        // Load all components from API
        const response = await fetch(`${API_URL}/stocks`);
        const result = await response.json();
        allStocks = result.data;
        
        // Display with current filters
        displayStocks();
    } catch (error) {
        console.error('Error loading stocks:', error);
        alert('Failed to load components');
    }
}

function displayStocks() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
    const categoryId = document.getElementById('categoryFilter').value;
    const statusFilter = document.getElementById('stockStatusFilter').value;
    
    // Filter components based on search, category, and status
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
            container.innerHTML = '<div class="empty-state"><h3>No components found</h3><p>Try adjusting your search or filters</p></div>';
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
                        <th>Created At</th>
                        <th>Updated At</th>
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
                                <td>${new Date(stock.created_at).toLocaleString()}</td>
                                <td>${new Date(stock.updated_at).toLocaleString()}</td>
                                <td>
                                    <button class="btn btn-sm" onclick="openUsageModal(${stock.id}, '${escapeHtml(stock.name)}', ${stock.quantity})" title="Use Component">Use</button>
                                    <button class="btn btn-edit btn-sm" onclick="editStock(${stock.id})" title="Edit">✏️</button>
                                    <button class="btn btn-danger btn-sm" onclick="deleteStock(${stock.id}, '${escapeHtml(stock.name)}')" title="Delete">❌</button>
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
            let quantityColor = '#10b981'; // Default for OK
            if (stock.quantity === 0) {
                statusBadge = '<div class="badge" style="background: #ef4444;">🔴 Out of Stock</div>';
                quantityColor = '#ef4444';
            } else if (stock.quantity <= 5) {
                statusBadge = '<div class="badge" style="background: #f59e0b;">⚠️ Critical Stock</div>';
                quantityColor = '#f59e0b';
            }
            
            return `
            <div class="card" onclick="showStockDetails(${stock.id})">
                ${stock.image_path ? `<div class="card-image"><img src="${stock.image_path}" alt="${escapeHtml(stock.name)}" loading="lazy"></div>` : ''}
                <div class="card-header">
                    <h3>${escapeHtml(stock.name)}</h3>
                    <div class="card-actions">
                        <button class="btn btn-edit" onclick="event.stopPropagation(); editStock(${stock.id})" title="Edit">✏️</button>
                        <button class="btn btn-danger" onclick="event.stopPropagation(); deleteStock(${stock.id}, '${escapeHtml(stock.name)}')" title="Delete">❌</button>
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
                    <div class="quantity" style="color: ${quantityColor};">
                        ${stock.quantity} <span class="unit">${escapeHtml(stock.unit || 'pcs')}</span>
                    </div>
                    <button class="btn btn-primary" onclick="event.stopPropagation(); openUsageModal(${stock.id}, '${escapeHtml(stock.name)}', ${stock.quantity})" ${stock.quantity === 0 ? 'disabled' : ''}>
                        Use Item
                    </button>
                </div>
            </div>
            `;
        }).join('');
    }
}

function openStockModal(stock = null, quickAdd = false) {
    console.log('openStockModal called');

    editingStockId = stock ? stock.id : null;
    document.getElementById('stockModalTitle').textContent = editingStockId ? 'Edit Component' : 'Add Component';
    
    // Pre-fill with common values for quick add
    const savedUnit = localStorage.getItem('lastUnit') || 'pcs';
    const savedLocation = localStorage.getItem('lastLocation') || '';
    
    document.getElementById('stockId').value = stock?.id || '';
    document.getElementById('stockName').value = stock?.name || '';
    document.getElementById('stockQuantity').value = stock?.quantity || (quickAdd ? 1 : 0);
    document.getElementById('stockUnit').value = stock?.unit || savedUnit;
    document.getElementById('stockLocation').value = stock?.location || (quickAdd ? 'Office' : savedLocation);
    document.getElementById('stockDescription').value = stock?.description || '';
    
    // Show modal IMMEDIATELY
    const modal = document.getElementById('stockModal');
    modal.classList.add('active');
    modal.style.display = 'flex';
    
    // Set category dropdown value from pre-loaded data
    if (stock) {
        document.getElementById('stockCategory').value = stock.category_id;
    } else if (quickAdd) {
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
    
    // Auto-focus on name field for faster input
    setTimeout(() => {
        const nameField = document.getElementById('stockName');
        if (nameField) {
            nameField.focus();
        }
    }, 150);
}

function closeStockModal() {
    const modal = document.getElementById('stockModal');
    modal.classList.remove('active');

    if (isWebView) {
        // Use aggressive style clearing for webview
        modal.style.cssText = 'display: none !important;';
    } else {
        modal.style.display = 'none';
    }

    // Reset forced styles
    modal.style.position = '';
    modal.style.top = '';
    modal.style.left = '';
    modal.style.width = '';
    modal.style.height = '';
    modal.style.zIndex = '';
    modal.style.backgroundColor = '';
    modal.style.justifyContent = '';
    modal.style.alignItems = '';
    modal.style.padding = '';

    // Reset modal content styles
    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        modalContent.style.position = '';
        modalContent.style.zIndex = '';
        modalContent.style.display = '';
        modalContent.style.visibility = '';
        modalContent.style.backgroundColor = '';
        modalContent.style.borderRadius = '';
        modalContent.style.maxWidth = '';
        modalContent.style.width = '';
        modalContent.style.boxShadow = '';
    }
    
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

// Add event listeners for filters
document.getElementById('categoryFilter')?.addEventListener('change', displayStocks);
document.getElementById('stockStatusFilter')?.addEventListener('change', displayStocks);
document.getElementById('searchInput')?.addEventListener('input', displayStocks);

// Stock form submission
document.getElementById('stockForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
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
            alert(result.message || 'Failed to save component');
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
        console.error('Error saving component:', error);
        alert('Failed to save component');
    }
});

async function showStockDetails(stockId) {
    try {
        const response = await fetch(`${API_URL}/stocks/${stockId}`);
        const result = await response.json();

        if (result.success && result.data) {
            const stock = result.data;

            // Format timestamps
            const createdDate = new Date(stock.created_at).toLocaleString();
            const updatedDate = new Date(stock.updated_at).toLocaleString();

            let content = `
                <div style="text-align: center; margin-bottom: 1rem;">
                    ${stock.image_path ? `<img src="${stock.image_path}" alt="${escapeHtml(stock.name)}" style="max-width: 100%; max-height: 200px; border-radius: 8px; margin-bottom: 1rem;">` : ''}
                    <h4 style="margin-bottom: 0.5rem; color: #333;">${escapeHtml(stock.name)}</h4>
                    <div class="badge">${escapeHtml(stock.category_name)}</div>
                </div>

                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h5 style="margin-bottom: 0.5rem; color: #333;">📋 Details</h5>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9em;">
                        <div><strong>Quantity:</strong> ${stock.quantity} ${escapeHtml(stock.unit || 'pcs')}</div>
                        <div><strong>Location:</strong> ${escapeHtml(stock.location || '-')}</div>
                        <div><strong>Created:</strong> ${createdDate}</div>
                        <div><strong>Updated:</strong> ${updatedDate}</div>
                    </div>
                    ${stock.description ? `<p style="margin-top: 1rem; color: #666;">${escapeHtml(stock.description)}</p>` : ''}
                </div>
            `;

            document.getElementById('stockDetailsContent').innerHTML = content;
            document.getElementById('stockDetailsModal').classList.add('active');
            document.getElementById('stockDetailsModal').style.display = 'flex';
        } else {
            alert('Failed to load component details.');
        }
    } catch (error) {
        console.error('Error loading component details:', error);
        alert('Failed to load component details.');
    }
}

function closeStockDetailsModal() {
    const modal = document.getElementById('stockDetailsModal');
    modal.classList.remove('active');
    modal.style.display = 'none';
}

async function editStock(id) {
    try {
        const response = await fetch(`${API_URL}/stocks/${id}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            openStockModal(result.data);
        } else {
            alert('Component not found');
        }
    } catch (error) {
        console.error('Error loading component:', error);
        alert('Failed to load component details');
    }
}

async function deleteStock(id, name) {
    const message = `Are you sure you want to delete the component "${name}"? This will permanently remove it from your inventory.`;
    openConfirmModal(message, async () => {
    try {
        const response = await fetch(`${API_URL}/stocks/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            loadStocks();
        } else {
            alert(result.message || 'Failed to delete component');
        }
    } catch (error) {
        console.error('Error deleting component:', error);
        alert('Failed to delete component');
    }
    });
}

// Usage tracking
let currentUsageStockId = null;
let currentUsageStockName = '';
let currentUsageStockQuantity = 0;

function openUsageModal(id, name, currentQty) {
    currentUsageStockId = id;
    currentUsageStockName = name;
    currentUsageStockQuantity = currentQty;
    
    document.getElementById('usageModalText').textContent = `Using: ${name} (Available: ${currentQty})`;
    
    // Set max to prevent using more than available
    const usageInput = document.getElementById('usageQuantity');
    usageInput.max = currentQty;
    usageInput.value = '1';
    
    const usageModal = document.getElementById('usageModal');
    usageModal.classList.add('active');
    usageModal.style.display = 'flex'; // Force display for webview compatibility
    
    // Focus on input after modal opens
    setTimeout(() => {
        document.getElementById('usageQuantity').focus();
    }, 100);
}

function closeUsageModal() {
    const modal = document.getElementById('usageModal');
    modal.classList.remove('active');
    modal.style.display = 'none'; // Force hide for webview compatibility
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
        // Get current component details
        const response = await fetch(`${API_URL}/stocks/${currentUsageStockId}`);
        const result = await response.json();
        
        if (!result.success) {
            alert('Failed to load component details');
            return;
        }
        
        const stock = result.data;
        const newQuantity = stock.quantity - usedQty;
        
        // Update component with new quantity
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
            alert(updateResult.message || 'Failed to update component');
        }
    } catch (error) {
        console.error('Error using component:', error);
        alert('Failed to update component');
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
    
    // Show initial progress indicator
    const thinkingId = addChatMessage('assistant', '⏳ Processing your message...');
    
    try {
        // Use streaming endpoint for real-time progress updates
        const response = await fetch(`${API_URL}/ai/ask/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question,
                conversation_id: currentConversationId
            })
        });

        if (!response.ok) {
            removeChatMessage(thinkingId);
            const msg = `❌ Error: ${response.status} ${response.statusText}`;
            addChatMessage('assistant', msg);
            return;
        }

        // Parse SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let result = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;

                // Parse SSE format: event: type\ndata: json
                const eventMatch = line.match(/^event:\s*(\w+)/m);
                const dataMatch = line.match(/^data:\s*(.+)$/ms);
                
                if (!eventMatch || !dataMatch) continue;

                const eventType = eventMatch[1];
                const dataStr = dataMatch[1].trim();

                try {
                    const data = JSON.parse(dataStr);

                    if (eventType === 'progress') {
                        // Update progress message in real-time
                        updateChatMessage(thinkingId, `⏳ ${data.message}`);
                    } else if (eventType === 'result') {
                        result = data;
                    } else if (eventType === 'error') {
                        removeChatMessage(thinkingId);
                        addChatMessage('assistant', `❌ ${data.message || 'An error occurred'}`);
                        return;
                    }
                } catch (e) {
                    console.error('Error parsing SSE data:', e);
                }
            }
        }

        // Remove thinking message
        removeChatMessage(thinkingId);

        if (!result) {
            addChatMessage('assistant', '❌ Error: No response received from server');
            return;
        }

        if (result.success) {
            // Create conversation if it doesn't exist
            if (!currentConversationId) {
                try {
                    const convResponse = await fetch(`${API_URL}/conversations`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title: 'New Conversation' })
                    });
                    const convResult = await convResponse.json();
                    if (convResult.success && convResult.data) {
                        currentConversationId = convResult.data.id;
                    }
                } catch (error) {
                    console.error('Error creating conversation:', error);
                }
            }
            
            // Update conversation_id if returned from AI service
            if (result.data && result.data.conversation_id) {
                currentConversationId = result.data.conversation_id;
            }
            
            // Save user message to conversation
            if (currentConversationId) {
                try {
                    await fetch(`${API_URL}/conversations/${currentConversationId}/messages`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ role: 'user', message: question })
                    });
                } catch (error) {
                    console.error('Error saving user message:', error);
                }
            }
            
            let assistantText = result.data.answer || '';
            if (result.data && result.data.model) {
                assistantText += `\n\n🧠 Model: ${result.data.model}`;
            }
            
            let fullAssistantMessage = assistantText;
            if (Array.isArray(result.data?.inventory) && result.data.inventory.length > 0) {
                addChatTable('assistant', result.data.inventory);
                // Include inventory table in saved message
                const tableText = `\n\nInventory Data:\n${JSON.stringify(result.data.inventory, null, 2)}`;
                fullAssistantMessage += tableText;
            }

            // Render specs table if provided by backend
            if (result.data?.specs && typeof result.data.specs === 'object') {
                const specs = result.data.specs;
                const headers = ['Spec', 'Value'];
                const th = (h) => `<th style="text-align:left;padding:6px 8px;border-bottom:1px solid #cbd5e1;">${h}</th>`;
                const tr = (k, v) => `<tr><td style="padding:6px 8px;border-bottom:1px solid #e2e8f0;width:40%;font-weight:600;">${escapeHtml(k)}</td><td style="padding:6px 8px;border-bottom:1px solid #e2e8f0;">${escapeHtml(String(v))}</td></tr>`;
                let rows = '';
                Object.keys(specs).forEach(k => { rows += tr(k, specs[k]); });
                const html = `
                    <div style="margin-bottom:1rem;padding:0.75rem;border-radius:8px;background:#e2e8f0;color:#1e293b;max-width:100%;margin-right:auto;overflow-x:auto;">
                        <div style="font-weight:600;margin:4px 0 6px;">Key Specifications</div>
                        <table style="border-collapse:collapse;width:100%;font-size:0.95rem;">
                            <thead><tr>${headers.map(th).join('')}</tr></thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>`;
                addChatMessage('assistant', html);
                fullAssistantMessage += `\n\nSpecs: ${JSON.stringify(specs, null, 2)}`;
            }

            // Add Open PDF button if datasheet info is present
            if (result.data?.datasheet?.open_url) {
                const url = result.data.datasheet.open_url;
                const name = result.data.datasheet.component_name || 'Datasheet';
                const btnHtml = `
                    <div style="margin-bottom:0.5rem;padding:0.4rem;border-radius:8px;background:#e2e8f0;color:#1e293b;max-width:80%;margin-right:auto;">
                        <div style="margin-bottom:0.2rem;font-size:0.9rem;">📄 Datasheet available for <strong>${escapeHtml(name)}</strong></div>
                        <a href="${url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="display:inline-flex;align-items:center;gap:8px;text-decoration:none;">
                            <span>Open PDF</span>
                            <span aria-hidden="true">↗</span>
                        </a>
                    </div>`;
                addChatMessage('assistant', btnHtml);
                // Also append to saved assistant message
                fullAssistantMessage += `\n\nOpen PDF: ${url}`;
            }
            
            if (assistantText) {
                addChatMessage('assistant', assistantText);
            }
            
            // Save assistant message to conversation
            if (currentConversationId && fullAssistantMessage) {
                try {
                    await fetch(`${API_URL}/conversations/${currentConversationId}/messages`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ role: 'assistant', message: fullAssistantMessage })
                    });
                    // Refresh conversations list to update message counts
                    await loadConversations();
                } catch (error) {
                    console.error('Error saving assistant message:', error);
                }
            }
        } else {
            addChatMessage('assistant', '❌ ' + result.message);
        }
    } catch (error) {
        removeChatMessage(thinkingId);
        addChatMessage('assistant', '❌ Error: Could not connect to AI service');
        console.error('AI request error:', error);
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
    msgDiv.innerHTML = message;
    
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

function updateChatMessage(msgId, newMessage) {
    const msg = document.getElementById(msgId);
    if (msg) {
        msg.innerHTML = newMessage;
    }
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
    const renameModal = document.getElementById('renameModal');
    renameModal.classList.add('active');
    renameModal.style.display = 'flex'; // Force display for webview compatibility
    document.getElementById('renameInput').focus();
    document.getElementById('renameInput').select();
}

function closeRenameModal() {
    const modal = document.getElementById('renameModal');
    modal.classList.remove('active');
    modal.style.display = 'none'; // Force hide for webview compatibility
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
    const confirmModal = document.getElementById('confirmModal');
    confirmModal.classList.add('active');
    confirmModal.style.display = 'flex'; // Force display for webview compatibility
    
    // Focus on confirm button
    setTimeout(() => {
        document.getElementById('confirmOkBtn').focus();
    }, 100);
}

function closeConfirmModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.remove('active');
    modal.style.display = 'none'; // Force hide for webview compatibility
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
    const alertModal = document.getElementById('alertModal');
    alertModal.classList.add('active');
    alertModal.style.display = 'flex'; // Force display for webview compatibility
    
    // Focus on OK button
    setTimeout(() => {
        document.getElementById('alertOkBtn').focus();
    }, 100);
}

function closeAlertModal() {
    const modal = document.getElementById('alertModal');
    modal.classList.remove('active');
    modal.style.display = 'none'; // Force hide for webview compatibility
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

// Category Details Modal
async function showCategoryDetails(categoryId) {
    try {
        const response = await fetch(`${API_URL}/categories/${categoryId}`);
        const result = await response.json();

        if (result.success && result.data) {
            const category = result.data;
            const stats = category.statistics || {};

            // Format timestamps
            const createdDate = new Date(category.created_at).toLocaleString();
            const updatedDate = new Date(category.updated_at).toLocaleString();

            let content = `
                <div style="margin-bottom: 1.5rem;">
                    <h4 style="margin-bottom: 0.5rem; color: #333;">${escapeHtml(category.name)}</h4>
                    ${category.description ? `<p style="color: #666; margin-bottom: 1rem;">${escapeHtml(category.description)}</p>` : ''}
                </div>

                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h5 style="margin-bottom: 0.5rem; color: #333;">📅 Timestamps</h5>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9em;">
                        <div><strong>Created:</strong> ${createdDate}</div>
                        <div><strong>Updated:</strong> ${updatedDate}</div>
                    </div>
                </div>

                <div style="background: #e8f4f8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h5 style="margin-bottom: 0.5rem; color: #333;">📊 Statistics</h5>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem; font-size: 0.9em;">
                        <div style="text-align: center; padding: 0.5rem; background: white; border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: bold; color: #007bff;">${stats.total_items || 0}</div>
                            <div style="color: #666;">Total Items</div>
                        </div>
                        <div style="text-align: center; padding: 0.5rem; background: white; border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: bold; color: #28a745;">${stats.total_quantity || 0}</div>
                            <div style="color: #666;">Total Quantity</div>
                        </div>
                        <div style="text-align: center; padding: 0.5rem; background: white; border-radius: 4px;">
                            <div style="font-size: 1.2em; font-weight: bold; color: #dc3545;">${stats.low_stock_count || 0}</div>
                            <div style="color: #666;">Low Stock</div>
                        </div>
                    </div>
                </div>
            `;

            // Add unit breakdown if available
            if (stats.unit_breakdown && Object.keys(stats.unit_breakdown).length > 0) {
                content += `
                    <div style="background: #f0f8e8; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <h5 style="margin-bottom: 0.5rem; color: #333;">📦 Unit Breakdown</h5>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.5rem;">
                `;

                Object.entries(stats.unit_breakdown).forEach(([unit, data]) => {
                    content += `
                        <div style="padding: 0.5rem; background: white; border-radius: 4px; text-align: center;">
                            <div style="font-weight: bold; color: #333;">${unit}</div>
                            <div style="font-size: 0.9em; color: #666;">${data.count} items, ${data.quantity} total</div>
                        </div>
                    `;
                });

                content += `
                        </div>
                    </div>
                `;
            }

            // Add stock items list if available
            if (stats.items && stats.items.length > 0) {
                content += `
                    <div style="background: #fff8e8; padding: 1rem; border-radius: 8px;">
                        <h5 style="margin-bottom: 0.5rem; color: #333;">📋 Stock Items</h5>
                        <div style="max-height: 200px; overflow-y: auto;">
                `;

                stats.items.forEach(item => {
                    const quantityColor = item.quantity <= 5 ? '#dc3545' : item.quantity <= 10 ? '#ffc107' : '#28a745';
                    content += `
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: white; margin-bottom: 0.25rem; border-radius: 4px;">
                            <div>
                                <strong>${escapeHtml(item.name)}</strong>
                                ${item.location ? `<br><small style="color: #666;">📍 ${escapeHtml(item.location)}</small>` : ''}
                            </div>
                            <div style="text-align: right;">
                                <div style="font-weight: bold; color: ${quantityColor};">${item.quantity} ${item.unit || 'pcs'}</div>
                            </div>
                        </div>
                    `;
                });

                content += `
                        </div>
                    </div>
                `;
            }

            document.getElementById('categoryDetailsContent').innerHTML = content;
            const categoryDetailsModal = document.getElementById('categoryDetailsModal');
            categoryDetailsModal.classList.add('active');
            categoryDetailsModal.style.display = 'flex'; // Force display for webview compatibility
        } else {
            alert('Failed to load category details');
        }
    } catch (error) {
        console.error('Error loading category details:', error);
        alert('Failed to load category details');
    }
}

function closeCategoryDetailsModal() {
    const modal = document.getElementById('categoryDetailsModal');
    modal.classList.remove('active');
    modal.style.display = 'none'; // Force hide for webview compatibility
}

// About Modal
function openAboutModal() {
    const modal = document.getElementById('aboutModal');
    modal.classList.add('active');
    modal.style.display = 'flex';

    // Check server status
    const statusEl = document.getElementById('serverStatus');
    fetch(`${API_URL}/health`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'healthy') {
                statusEl.textContent = 'Online';
                statusEl.style.color = '#28a745';
            } else {
                statusEl.textContent = 'Offline';
                statusEl.style.color = '#dc3545';
            }
        })
        .catch(() => {
            statusEl.textContent = 'Offline';
            statusEl.style.color = '#dc3545';
        });
}

function closeAboutModal() {
    const modal = document.getElementById('aboutModal');
    modal.classList.remove('active');
    modal.style.display = 'none';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded. Pre-loading categories.');
    loadCategoriesForSelect();
    loadStocks();

    // Check if the page was loaded to show the about modal
    if (window.location.pathname === '/about') {
        openAboutModal();
        // Optional: remove /about from URL without reloading
        window.history.replaceState({}, document.title, "/");
    }
});
