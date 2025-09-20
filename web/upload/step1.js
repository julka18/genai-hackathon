// Firebase (CDN)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { doc, getFirestore, serverTimestamp, setDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// Config
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

// DOM
const $ = (s) => document.querySelector(s);
const notice = $("#notice");
$("#logout-btn")?.addEventListener("click", () => signOut(auth));

let user = null;
onAuthStateChanged(auth, (u) => {
    if (!u) return (window.location.href = "/web/auth/index.html");
    user = u;
    $("#welcome-user").textContent = `Welcome ${u.phoneNumber || "artisan"}!`;
});

function setNotice(m, ok = false) { notice.textContent = m; notice.style.color = ok ? "#22c55e" : "#9aa0aa"; }

function collect() {
    const title = $("#productName").value.trim();
    const category = $("#category").value.trim();
    const enDesc = $("#description").value.trim();
    const low = Number($("#priceLow").value || 0);
    const high = Number($("#priceHigh").value || 0);
    const hashtags = $("#hashtags").value.trim();
    const cta = $("#ctaWhatsapp").value.trim();

    return { title, category, enDesc, low, high, hashtags, cta };
}

async function saveDraft(goNext) {
    if (!user) return setNotice("Please login again.");

    const f = collect();
    if (!f.title) return setNotice("Enter a product name.");
    if (!f.category) return setNotice("Choose a category.");

    // New doc id (client-side): keep it stable across Next
    const pid = crypto.randomUUID();

    const payload = {
        ownerUid: user.uid,
        slug: (f.title || "product").toLowerCase().replace(/\s+/g, "-"),
        titles: { en: f.title, hi: "" },
        description: { en: f.enDesc, hi: "" },
        category: f.category,
        price: { low: f.low, high: f.high, currency: "INR" },
        hashtags: f.hashtags ? f.hashtags.split(/\s+/).filter(Boolean) : [],
        cta: { whatsapp: f.cta },
        status: "draft",
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
    };

    await setDoc(doc(db, "products", pid), payload, { merge: true });
    setNotice("Draft saved.", true);

    if (goNext) {
        window.location.href = `/web/upload/photos.html?pid=${encodeURIComponent(pid)}`;
    }
}

$("#btn-save-draft")?.addEventListener("click", () => saveDraft(false));
$("#btn-next")?.addEventListener("click", () => saveDraft(true));
