import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore, collection, doc, getDoc, setDoc, updateDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

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

// Check authentication status
onAuthStateChanged(auth, (user) => {
    if (!user) {
        window.location.href = "/web/auth/index.html";
    } else {
        currentUser = user;
        updateWelcomeText(user);
        loadUserProfile();
    }
});

// Update welcome text
async function updateWelcomeText(user) {
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

// Load user profile
async function loadUserProfile() {
    try {
        const userRef = doc(db, "users", currentUser.uid);
        const userSnap = await getDoc(userRef);
        
        if (userSnap.exists()) {
            const userData = userSnap.data();
            populateProfileForm(userData);
        } else {
            // Create initial profile
            const initialData = {
                firstName: currentUser.displayName?.split(' ')[0] || '',
                lastName: currentUser.displayName?.split(' ').slice(1).join(' ') || '',
                email: currentUser.email || '',
                phone: currentUser.phoneNumber || '',
                businessName: '',
                bio: '',
                address: '',
                city: '',
                state: '',
                pincode: '',
                country: 'India',
                gstNumber: '',
                createdAt: new Date(),
                updatedAt: new Date()
            };
            
            await setDoc(userRef, initialData);
            populateProfileForm(initialData);
        }
        
        updateUserInitials();
        
    } catch (error) {
        console.error('Error loading user profile:', error);
        setNotice("Error loading profile", 'error');
    }
}

// Populate profile form
function populateProfileForm(userData) {
    $("firstName").value = userData.firstName || '';
    $("lastName").value = userData.lastName || '';
    $("email").value = userData.email || '';
    $("phone").value = userData.phone || '';
    $("businessName").value = userData.businessName || '';
    $("bio").value = userData.bio || '';
    $("address").value = userData.address || '';
    $("city").value = userData.city || '';
    $("state").value = userData.state || '';
    $("pincode").value = userData.pincode || '';
    $("country").value = userData.country || 'India';
    $("gstNumber").value = userData.gstNumber || '';
}

// Update user initials
function updateUserInitials() {
    const firstName = $("firstName").value || '';
    const lastName = $("lastName").value || '';
    const initials = (firstName.charAt(0) + lastName.charAt(0)).toUpperCase() || 'U';
    $("user-initials").textContent = initials;
}

// Handle profile form submission
$("profile-form").onsubmit = async (e) => {
    e.preventDefault();
    
    try {
        const profileData = {
            firstName: $("firstName").value.trim(),
            lastName: $("lastName").value.trim(),
            email: $("email").value.trim(),
            phone: $("phone").value.trim(),
            businessName: $("businessName").value.trim(),
            bio: $("bio").value.trim(),
            updatedAt: new Date()
        };
        
        const userRef = doc(db, "users", currentUser.uid);
        await updateDoc(userRef, profileData);
        
        setNotice("Profile updated successfully", 'success');
        updateUserInitials();
        
    } catch (error) {
        console.error('Error updating profile:', error);
        setNotice("Error updating profile", 'error');
    }
};

// Handle business form submission
$("business-form").onsubmit = async (e) => {
    e.preventDefault();
    
    try {
        const businessData = {
            address: $("address").value.trim(),
            city: $("city").value.trim(),
            state: $("state").value.trim(),
            pincode: $("pincode").value.trim(),
            country: $("country").value.trim(),
            gstNumber: $("gstNumber").value.trim(),
            updatedAt: new Date()
        };
        
        const userRef = doc(db, "users", currentUser.uid);
        await updateDoc(userRef, businessData);
        
        setNotice("Business information updated successfully", 'success');
        
    } catch (error) {
        console.error('Error updating business info:', error);
        setNotice("Error updating business information", 'error');
    }
};

// Handle FAQ toggles
document.addEventListener('DOMContentLoaded', () => {
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            const isActive = faqItem.classList.contains('active');
            
            // Close all FAQ items
            document.querySelectorAll('.faq-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Toggle current item
            if (!isActive) {
                faqItem.classList.add('active');
            }
        });
    });
    
    // Update initials when name fields change
    $("firstName").addEventListener('input', updateUserInitials);
    $("lastName").addEventListener('input', updateUserInitials);
});

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
