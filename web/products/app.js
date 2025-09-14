import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore, collection, query, where, getDocs, doc, updateDoc, deleteDoc, orderBy, getDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBGdIxeWZnndbSDH78rzI_9B6Auf-nrrT8",
    authDomain: "meow-2fe74.firebaseapp.com",
    projectId: "meow-2fe74",
    storageBucket: "meow-2fe74.appspot.com",
    messagingSenderId: "519498484362",
    appId: "1:519498484362:web:791dcab7d9160d48f7bb73",
    measurementId: "G-Y1FHJWBMN4"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Utility functions
const $ = (id) => document.getElementById(id);
const setNotice = (msg, type = 'info') => {
    const n = $("notice");
    if (n) {
        n.textContent = msg;
        n.className = type;
    }
};

let currentUser = null;
let products = [];
let editingProduct = null;

// Check authentication status
onAuthStateChanged(auth, (user) => {
    if (!user) {
        window.location.href = "/web/auth/index.html";
    } else {
        currentUser = user;
        loadUserProfile(user);
        loadProducts();
    }
});

// Load user profile
async function loadUserProfile(user) {
    try {
        const userDoc = await getDoc(doc(db, "users", user.uid));
        if (userDoc.exists()) {
            const userData = userDoc.data();
            const firstName = userData.firstName || 'User';
            const welcomeText = document.querySelector('.welcome-text');
            if (welcomeText) {
                welcomeText.textContent = `Welcome ${firstName}!`;
            }
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

// Load products
async function loadProducts() {
    try {
        const productsRef = collection(db, "products");
        const q = query(productsRef, orderBy("createdAt", "desc"));
        const querySnapshot = await getDocs(q);
        
        products = [];
        querySnapshot.forEach((doc) => {
            products.push({ id: doc.id, ...doc.data() });
        });
        
        updateProductStats();
        displayProducts();
        
    } catch (error) {
        console.error('Error loading products:', error);
        setNotice("Error loading products", 'error');
    }
}

// Update product statistics
function updateProductStats() {
    const totalProducts = products.length;
    const publishedProducts = products.filter(p => p.status === 'published').length;
    const draftProducts = products.filter(p => p.status === 'draft').length;
    
    $("total-products-count").textContent = totalProducts;
    $("active-products-count").textContent = publishedProducts;
    $("draft-products-count").textContent = draftProducts;
}

// Display products
function displayProducts() {
    const grid = $("products-grid");
    const emptyState = $("empty-state");
    
    if (products.length === 0) {
        grid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    grid.style.display = 'grid';
    emptyState.style.display = 'none';
    
    grid.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-image">
                <span>📦</span>
                <span class="product-status ${product.status}">${product.status}</span>
            </div>
            <div class="product-info">
                <h3 class="product-name">${product.productName}</h3>
                <span class="product-category">${product.category}</span>
                <p class="product-description">${product.description}</p>
                <p class="product-price">₹${product.price.toLocaleString()}</p>
                <div class="product-actions">
                    <button class="btn secondary" onclick="editProduct('${product.id}')">
                        <span class="btn-icon">✏️</span>
                        Edit
                    </button>
                    <button class="btn danger" onclick="deleteProduct('${product.id}')">
                        <span class="btn-icon">🗑️</span>
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Edit product
window.editProduct = function(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;
    
    editingProduct = product;
    
    // Populate form
    $("edit-productName").value = product.productName;
    $("edit-category").value = product.category;
    $("edit-description").value = product.description;
    $("edit-price").value = product.price;
    $("edit-quantity").value = product.quantity;
    
    // Show modal
    $("edit-modal").classList.add("show");
};

// Delete product
window.deleteProduct = async function(productId) {
    if (!confirm('Are you sure you want to delete this product?')) return;
    
    try {
        await deleteDoc(doc(db, "products", productId));
        products = products.filter(p => p.id !== productId);
        updateProductStats();
        displayProducts();
        setNotice("Product deleted successfully", 'success');
    } catch (error) {
        console.error('Error deleting product:', error);
        setNotice("Error deleting product", 'error');
    }
};

// Handle edit form submission
$("edit-form").onsubmit = async (e) => {
    e.preventDefault();
    
    if (!editingProduct) return;
    
    try {
        const updatedData = {
            productName: $("edit-productName").value.trim(),
            category: $("edit-category").value,
            description: $("edit-description").value.trim(),
            price: parseInt($("edit-price").value),
            quantity: parseInt($("edit-quantity").value),
            updatedAt: new Date()
        };
        
        await updateDoc(doc(db, "products", editingProduct.id), updatedData);
        
        // Update local data
        const productIndex = products.findIndex(p => p.id === editingProduct.id);
        if (productIndex !== -1) {
            products[productIndex] = { ...products[productIndex], ...updatedData };
        }
        
        updateProductStats();
        displayProducts();
        closeModal();
        setNotice("Product updated successfully", 'success');
        
    } catch (error) {
        console.error('Error updating product:', error);
        setNotice("Error updating product", 'error');
    }
};

// Close modal
function closeModal() {
    $("edit-modal").classList.remove("show");
    editingProduct = null;
}

// Modal event listeners
$("modal-close").onclick = closeModal;
$("cancel-edit").onclick = closeModal;

// Close modal when clicking outside
$("edit-modal").onclick = (e) => {
    if (e.target === $("edit-modal")) {
        closeModal();
    }
};

// Handle background video loading
document.addEventListener('DOMContentLoaded', () => {
    const video = document.querySelector('.bg-video');
    const fallback = document.querySelector('.bg-fallback');
    
    if (video) {
        video.addEventListener('error', () => {
            console.log('Video failed to load, using fallback image');
            if (fallback) {
                fallback.style.display = 'block';
            }
        });
        
        if (window.innerWidth <= 768) {
            video.pause();
        }
    }
});

// Logout functionality
$("logout-btn").onclick = async () => {
    try {
        await signOut(auth);
        window.location.href = "/web/auth/index.html";
    } catch (error) {
        console.error('Logout error:', error);
        setNotice("Error logging out. Please try again.", 'error');
    }
};
