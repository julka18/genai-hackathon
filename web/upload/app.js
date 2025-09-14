import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore, collection, addDoc, serverTimestamp, doc, getDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// Firebase configuration (same as auth page)
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
    n.textContent = msg;
    n.className = type;
};

// Check authentication status
onAuthStateChanged(auth, (user) => {
    if (!user) {
        // User not authenticated, redirect to login
        window.location.href = "/web/auth/index.html";
    } else {
        loadUserProfile(user);
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

// Handle background video loading (same as auth page)
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
        
        video.addEventListener('loadeddata', () => {
            console.log('Background video loaded successfully');
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

// File upload handling
let selectedFiles = [];

const uploadArea = $("upload-area");
const imageInput = $("image-input");
const imagePreview = $("image-preview");

// Drag and drop functionality
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
});

// Click to upload
uploadArea.addEventListener('click', () => {
    imageInput.click();
});

imageInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    handleFiles(files);
});

function handleFiles(files) {
    const validFiles = files.filter(file => {
        if (!file.type.startsWith('image/')) {
            setNotice("Please select only image files.", 'error');
            return false;
        }
        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            setNotice("File size must be less than 5MB.", 'error');
            return false;
        }
        return true;
    });

    if (selectedFiles.length + validFiles.length > 5) {
        setNotice("Maximum 5 images allowed.", 'error');
        return;
    }

    selectedFiles = [...selectedFiles, ...validFiles];
    displayImagePreviews();
    updateSummary();
}

function displayImagePreviews() {
    imagePreview.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            previewItem.innerHTML = `
                <img src="${e.target.result}" alt="Preview ${index + 1}">
                <button class="remove-btn" onclick="removeImage(${index})">×</button>
            `;
            imagePreview.appendChild(previewItem);
        };
        reader.readAsDataURL(file);
    });
}

// Remove image function (global for onclick)
window.removeImage = (index) => {
    selectedFiles.splice(index, 1);
    displayImagePreviews();
    updateSummary();
};

// Form submission
$("publish-product").onclick = async () => {
    console.log("Publish product button clicked");
    
    const formData = {
        productName: $("productName").value.trim(),
        category: $("category").value,
        description: $("description").value.trim(),
        price: parseInt($("price").value),
        quantity: parseInt($("quantity").value),
        images: selectedFiles.length,
        aiOptions: {
            generateCaption: $("generate-caption").checked,
            socialCampaigns: $("social-campaigns").checked,
            telegramPosts: $("telegram-posts").checked
        },
        createdAt: serverTimestamp(),
        status: 'published',
        userId: auth.currentUser?.uid || 'anonymous'
    };

    console.log("Form data:", formData);

    // Validation
    if (!formData.productName) return setNotice("Please enter product name.", 'error');
    if (!formData.category) return setNotice("Please select a category.", 'error');
    if (!formData.description) return setNotice("Please enter product description.", 'error');
    if (!formData.price || formData.price < 1) return setNotice("Please enter a valid price.", 'error');
    if (!formData.quantity || formData.quantity < 1) return setNotice("Please enter valid quantity.", 'error');
    if (selectedFiles.length === 0) return setNotice("Please upload at least one image.", 'error');

    const btn = $("publish-product");
    btn.classList.add("loading");
    btn.disabled = true;

    try {
        setNotice("Publishing your product...", 'info');
        console.log("Attempting to save to Firebase...");
        
        // Add product to Firestore
        const docRef = await addDoc(collection(db, "products"), formData);
        console.log("Product saved with ID:", docRef.id);
        
        // TODO: Handle image uploads to Firebase Storage
        // TODO: Generate AI content if options are enabled
        // TODO: Post to Telegram if option is enabled
        
        setNotice("✅ Product published successfully! Redirecting...", 'success');
        
        setTimeout(() => {
            // Reset form or redirect to product list
            resetForm();
            setNotice("Product published successfully!", 'success');
            // Redirect to products page
            window.location.href = "../products/index.html";
        }, 2000);
        
    } catch (error) {
        console.error('Error publishing product:', error);
        setNotice(`Error publishing product: ${error.message}`, 'error');
    } finally {
        btn.classList.remove("loading");
        btn.disabled = false;
    }
};

// Save as draft
$("save-draft").onclick = async () => {
    console.log("Save draft button clicked");
    
    const formData = {
        productName: $("productName").value.trim(),
        category: $("category").value,
        description: $("description").value.trim(),
        price: parseInt($("price").value) || 0,
        quantity: parseInt($("quantity").value) || 0,
        images: selectedFiles.length,
        aiOptions: {
            generateCaption: $("generate-caption").checked,
            socialCampaigns: $("social-campaigns").checked,
            telegramPosts: $("telegram-posts").checked
        },
        createdAt: serverTimestamp(),
        status: 'draft',
        userId: auth.currentUser?.uid || 'anonymous'
    };

    console.log("Draft data:", formData);

    const btn = $("save-draft");
    btn.classList.add("loading");
    btn.disabled = true;

    try {
        setNotice("Saving draft...", 'info');
        console.log("Attempting to save draft to Firebase...");
        
        const docRef = await addDoc(collection(db, "products"), formData);
        console.log("Draft saved with ID:", docRef.id);
        
        setNotice("✅ Draft saved successfully!", 'success');
        
    } catch (error) {
        console.error('Error saving draft:', error);
        setNotice(`Error saving draft: ${error.message}`, 'error');
    } finally {
        btn.classList.remove("loading");
        btn.disabled = false;
    }
};

// Update summary
function updateSummary() {
    const productName = $("productName").value.trim() || '-';
    const category = $("category").value || '-';
    const price = parseInt($("price").value) || 0;
    const quantity = parseInt($("quantity").value) || 0;
    const imageCount = selectedFiles.length;
    
    // Count enabled AI features
    const aiFeatures = [
        $("generate-caption").checked,
        $("social-campaigns").checked,
        $("telegram-posts").checked
    ].filter(Boolean).length;
    
    $("summary-name").textContent = productName;
    $("summary-category").textContent = category;
    $("summary-price").textContent = `₹${price.toLocaleString()}`;
    $("summary-quantity").textContent = quantity.toString();
    $("summary-images").textContent = `${imageCount}/5`;
    $("summary-ai").textContent = `${aiFeatures} enabled`;
    $("summary-total").textContent = `₹${(price * quantity).toLocaleString()}`;
}

// Add event listeners for summary updates
document.addEventListener('DOMContentLoaded', () => {
    // Update summary on input changes
    $("productName").addEventListener('input', updateSummary);
    $("category").addEventListener('change', updateSummary);
    $("price").addEventListener('input', updateSummary);
    $("quantity").addEventListener('input', updateSummary);
    $("generate-caption").addEventListener('change', updateSummary);
    $("social-campaigns").addEventListener('change', updateSummary);
    $("telegram-posts").addEventListener('change', updateSummary);
    
    // Initial summary update
    updateSummary();
});

// Reset form
function resetForm() {
    $("productName").value = '';
    $("category").value = '';
    $("description").value = '';
    $("price").value = '';
    $("quantity").value = '';
    selectedFiles = [];
    displayImagePreviews();
    $("generate-caption").checked = true;
    $("social-campaigns").checked = true;
    $("telegram-posts").checked = true;
    updateSummary();
}
