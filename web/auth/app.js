import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, RecaptchaVerifier, signInWithPhoneNumber } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { doc, getFirestore, serverTimestamp, setDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// ⚠️ Public by design. Do NOT put Admin keys here.
const firebaseConfig = {
    apiKey: "AIzaSyBGdIxeWZnndbSDH78rzI_9B6Auf-nrrT8",
    authDomain: "meow-2fe74.firebaseapp.com",
    projectId: "meow-2fe74",
    // ✅ correct domain:
    storageBucket: "meow-2fe74.appspot.com",
    messagingSenderId: "519498484362",
    appId: "1:519498484362:web:791dcab7d9160d48f7bb73",
    measurementId: "G-Y1FHJWBMN4"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
auth.useDeviceLanguage();
const db = getFirestore(app);

// Handle background video loading
document.addEventListener('DOMContentLoaded', () => {
    const video = document.querySelector('.bg-video');
    const fallback = document.querySelector('.bg-fallback');
    
    if (video) {
        // Check if video can play
        video.addEventListener('error', () => {
            console.log('Video failed to load, using fallback image');
            if (fallback) {
                fallback.style.display = 'block';
            }
        });
        
        // Handle video loading
        video.addEventListener('loadeddata', () => {
            console.log('Background video loaded successfully');
        });
        
        // Pause video on mobile to save battery (optional)
        if (window.innerWidth <= 768) {
            video.pause();
        }
    }
});

// Invisible reCAPTCHA required for Phone Auth
window.recaptchaVerifier = new RecaptchaVerifier(auth, "recaptcha-container", { size: "invisible" });

let confirmationResult = null;
const $ = (id) => document.getElementById(id);
const setNotice = (msg, ok = false) => {
    const n = $("notice");
    n.textContent = msg;
    n.style.color = ok ? "#A7F3D0" : "#9aa0aa";
};

$("send-otp").onclick = async () => {
    const phoneInput = $("phone").value.trim();
    const first = $("firstName").value.trim();
    const last = $("lastName").value.trim();

    if (!first || !last) return setNotice("Please enter first & last name.");
    if (!phoneInput) return setNotice("Please enter your phone number.");
    if (phoneInput.length !== 10) return setNotice("Please enter a valid 10-digit phone number.");

    // Add +91 prefix to the phone number
    const phone = "+91" + phoneInput;

    const btn = $("send-otp");
    btn.classList.add("loading");
    btn.disabled = true;

    try {
        setNotice("Sending OTP…");
        confirmationResult = await signInWithPhoneNumber(auth, phone, window.recaptchaVerifier);
        $("otp-block").classList.remove("hidden");
        setNotice("OTP sent. Enter the 6-digit code.");
    } catch (e) {
        console.error(e);
        setNotice("Could not send OTP: " + (e?.message || e));
    } finally {
        btn.classList.remove("loading");
        btn.disabled = false;
    }
};

$("verify-otp").onclick = async () => {
    if (!confirmationResult) return setNotice("Send OTP first.");
    const code = $("otp").value.trim();
    if (code.length < 6) return setNotice("Please enter the 6-digit OTP.");

    const btn = $("verify-otp");
    btn.classList.add("loading");
    btn.disabled = true;

    try {
        setNotice("Verifying…");
        const { user } = await confirmationResult.confirm(code);

        await setDoc(doc(db, "users", user.uid), {
            firstName: $("firstName").value.trim(),
            lastName: $("lastName").value.trim(),
            phone: "+91" + $("phone").value.trim(),
            createdAt: serverTimestamp()
        }, { merge: true });

        setNotice("✅ Verified. Profile saved. Redirecting…", true);
        setTimeout(() => (window.location.href = "/web/home/index.html"), 700);
    } catch (e) {
        console.error(e);
        setNotice("Wrong OTP or expired. Try again.");
    } finally {
        btn.classList.remove("loading");
        btn.disabled = false;
    }
};
