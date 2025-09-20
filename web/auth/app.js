// web/auth/app.js

// Firebase v10.12.0 (match your existing version)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
    getAuth,
    RecaptchaVerifier,
    signInWithPhoneNumber,
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import {
    doc,
    getFirestore,
    serverTimestamp,
    setDoc,
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// ---------- Firebase config (public by design) ----------
const firebaseConfig = {
    apiKey: "AIzaSyBGdIxeWZnndbSDH78rzI_9B6Auf-nrrT8",
    authDomain: "meow-2fe74.firebaseapp.com",
    projectId: "meow-2fe74",
    storageBucket: "meow-2fe74.appspot.com",
    messagingSenderId: "519498484362",
    appId: "1:519498484362:web:791dcab7d9160d48f7bb73",
    measurementId: "G-Y1FHJWBMN4",
};

// ---------- Init ----------
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
auth.useDeviceLanguage();
const db = getFirestore(app);

// ---------- Helpers ----------
const $ = (id) => document.getElementById(id);
const setNotice = (msg, ok = false) => {
    const n = $("notice");
    if (!n) return;
    n.textContent = msg;
    n.style.color = ok ? "#A7F3D0" : "#9aa0aa";
};

// Upsert users/{uid} with names + phone
async function upsertUserProfile({ firstName = "", lastName = "" }) {
    const u = auth.currentUser;
    if (!u) return;

    await setDoc(
        doc(db, "users", u.uid),
        {
            firstName,
            lastName,
            phone: u.phoneNumber || "",
            // createdAt set on first write; updatedAt always refreshed
            createdAt: serverTimestamp(),
            updatedAt: serverTimestamp(),
        },
        { merge: true }
    );
}

// ---------- Background video fallback (optional UI nicety) ----------
document.addEventListener("DOMContentLoaded", () => {
    const video = document.querySelector(".bg-video");
    const fallback = document.querySelector(".bg-fallback");

    if (!video) return;

    video.addEventListener("error", () => {
        if (fallback) fallback.style.display = "block";
    });

    video.addEventListener("loadeddata", () => {
        // console.log("Background video loaded");
    });

    if (window.innerWidth <= 768) video.pause();
});

// ---------- reCAPTCHA (required for Phone Auth) ----------
// Remove the invalid getRecaptchaVerifier() usage.
// Create the invisible verifier bound to a container div with id="recaptcha-container".
window.recaptchaVerifier = new RecaptchaVerifier(
    auth,
    "recaptcha-container",
    { size: "invisible" }
);

// ---------- OTP flow ----------
let confirmationResult = null;

$("send-otp").onclick = async () => {
    const phoneInput = $("phone")?.value.trim() || "";
    const first = $("firstName")?.value.trim() || "";
    const last = $("lastName")?.value.trim() || "";

    if (!first || !last) return setNotice("Please enter first & last name.");
    if (!phoneInput) return setNotice("Please enter your phone number.");
    if (phoneInput.length !== 10) return setNotice("Enter a valid 10-digit phone number.");

    const phone = "+91" + phoneInput; // India

    const btn = $("send-otp");
    btn?.classList.add("loading");
    if (btn) btn.disabled = true;

    try {
        setNotice("Sending OTP…");
        confirmationResult = await signInWithPhoneNumber(auth, phone, window.recaptchaVerifier);
        $("otp-block")?.classList.remove("hidden");
        setNotice("OTP sent. Enter the 6-digit code.");
    } catch (e) {
        console.error(e);
        setNotice("Could not send OTP: " + (e?.message || e));
    } finally {
        btn?.classList.remove("loading");
        if (btn) btn.disabled = false;
    }
};

$("verify-otp").onclick = async () => {
    if (!confirmationResult) return setNotice("Send OTP first.");
    const code = $("otp")?.value.trim() || "";
    if (code.length !== 6) return setNotice("Please enter the 6-digit OTP.");

    const btn = $("verify-otp");
    btn?.classList.add("loading");
    if (btn) btn.disabled = true;

    try {
        setNotice("Verifying…");
        const { user } = await confirmationResult.confirm(code);

        // Persist user profile in Firestore
        await upsertUserProfile({
            firstName: $("firstName")?.value.trim() || "",
            lastName: $("lastName")?.value.trim() || "",
        });

        // Keep UID for later pages (upload flow, drafts, etc.)
        localStorage.setItem("prachar_uid", user.uid);

        setNotice("✅ Verified. Profile saved. Redirecting…", true);
        setTimeout(() => {
            window.location.href = "/web/home/index.html";
        }, 700);
    } catch (e) {
        console.error(e);
        setNotice("Wrong or expired OTP. Try again.");
    } finally {
        btn?.classList.remove("loading");
        if (btn) btn.disabled = false;
    }
};
