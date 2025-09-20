import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { doc, getDoc, getFirestore } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

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
