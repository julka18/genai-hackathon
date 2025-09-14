import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore, collection, query, where, getDocs, orderBy, limit, doc, getDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

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

// Check authentication status
onAuthStateChanged(auth, (user) => {
    if (!user) {
        window.location.href = "/web/auth/index.html";
    } else {
        loadUserProfile(user);
        loadDashboardData();
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

// Load dashboard data
async function loadDashboardData() {
    try {
        const productsRef = collection(db, "products");
        const q = query(productsRef, orderBy("createdAt", "desc"));
        const querySnapshot = await getDocs(q);
        
        const products = [];
        querySnapshot.forEach((doc) => {
            products.push({ id: doc.id, ...doc.data() });
        });
        
        updateStats(products);
        loadRecentProducts(products.slice(0, 6));
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        setNotice("Error loading dashboard data", 'error');
    }
}

// Update statistics
function updateStats(products) {
    const totalProducts = products.length;
    const publishedProducts = products.filter(p => p.status === 'published').length;
    const totalRevenue = products
        .filter(p => p.status === 'published')
        .reduce((sum, p) => sum + (p.price * p.quantity), 0);
    
    // Calculate sales this month
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    const salesThisMonth = products
        .filter(p => p.status === 'published' && p.createdAt)
        .filter(p => {
            const productDate = p.createdAt.toDate ? p.createdAt.toDate() : new Date(p.createdAt);
            return productDate.getMonth() === currentMonth && productDate.getFullYear() === currentYear;
        })
        .reduce((sum, p) => sum + (p.price * p.quantity), 0);
    
    // Mock data for views and ratings (in real app, these would come from analytics)
    const totalViews = Math.floor(Math.random() * 1000) + 500;
    const avgRating = (Math.random() * 2 + 3).toFixed(1);
    
    $("total-products").textContent = totalProducts;
    $("total-revenue").textContent = `₹${totalRevenue.toLocaleString()}`;
    $("total-views").textContent = totalViews.toLocaleString();
    $("avg-rating").textContent = avgRating;
    
    // Update sales this month
    $("sales-this-month").textContent = `₹${salesThisMonth.toLocaleString()}`;
    
    // Update chart bar height (max 100% for visual representation)
    const maxSales = Math.max(salesThisMonth, 10000); // Set a reasonable max for visualization
    const chartHeight = Math.min((salesThisMonth / maxSales) * 100, 100);
    $("sales-chart-bar").style.height = `${chartHeight}%`;
}

// Load recent products
function loadRecentProducts(products) {
    const grid = $("recent-products-grid");
    if (!grid) return;
    
    if (products.length === 0) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-icon">📦</div><h3>No Products Yet</h3><p>Upload your first product to get started!</p></div>';
        return;
    }
    
    grid.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-image">
                <span>📦</span>
            </div>
            <div class="product-info">
                <h3 class="product-name">${product.productName}</h3>
                <span class="product-category">${product.category}</span>
                <p class="product-price">₹${product.price.toLocaleString()}</p>
            </div>
        </div>
    `).join('');
}

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
