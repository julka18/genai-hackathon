// /web/home/app.js
// ------------------------------------------------------------
// Firebase (CDN)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
    getAuth,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import {
    collection,
    doc, getDoc,
    getDocs,
    getFirestore,
    orderBy,
    query, where
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// ------------------------------------------------------------
// Firebase config
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

// ------------------------------------------------------------
// Small helpers
const $ = (id) => document.getElementById(id);
function setNotice(msg, type = "info") {
    const n = $("notice");
    if (!n) return;
    n.textContent = msg;
    n.className = type;
}
function escapeHtml(s) {
    return (s ?? "").toString().replace(/[&<>"']/g, m => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    })[m]);
}
function fmtPriceRange(p) {
    if (!p || (p.low == null && p.high == null)) return "";
    const low = (p.low ?? p.high ?? 0);
    const high = (p.high ?? p.low ?? 0);
    return `₹${Number(low).toLocaleString()} – ₹${Number(high).toLocaleString()}`;
}

/**
 * Detect mime type from base64 "magic header".
 * - JPEG starts with "/9j/"
 * - PNG starts with "iVBOR"
 * - WEBP can start with "UklGR" (WebP lossy) or "RIFF" (container)
 */
function detectMimeFromBase64(b64) {
    const head = (b64 || "").slice(0, 5);
    if (head.startsWith("/9j/")) return "image/jpeg";
    if (head.startsWith("iVBOR")) return "image/png";
    if (head.startsWith("UklGR") || head.startsWith("RIFF")) return "image/webp";
    return "image/jpeg"; // sensible default
}

/**
 * Build a displayable thumbnail src from your product's media.
 * Handles `url` or `base64`, strips prefixes/whitespace, and picks
 * the first image by `order` (if present) or index 0.
 */
function firstThumb(mediaArr) {
    if (Array.isArray(mediaArr) && mediaArr.length) {
        const sorted = [...mediaArr].sort((a, b) => (a?.order ?? 0) - (b?.order ?? 0));
        const m = sorted[0];

        if (m?.url && typeof m.url === "string") {
            return m.url;
        }

        if (m?.base64 && typeof m.base64 === "string") {
            const clean = m.base64.replace(/^data:.*;base64,/i, "").replace(/\s/g, "");
            const mime = m.mime || detectMimeFromBase64(clean);
            if (clean.length > 0) {
                return `data:${mime};base64,${clean}`;
            }
        }
    }
    return "/web/auth/placeholder.png";
}

// ------------------------------------------------------------
// Auth guard + boot
onAuthStateChanged(auth, async (user) => {
    if (!user) {
        window.location.href = "/web/auth/index.html";
        return;
    }
    await loadUserProfile(user);
    await loadDashboardData(user);
});

// ------------------------------------------------------------
// Profile (welcome name)
async function loadUserProfile(user) {
    try {
        const snap = await getDoc(doc(db, "users", user.uid));
        const first = snap.exists() ? (snap.data().firstName || "artisan") : "artisan";
        const w = document.querySelector(".welcome-text");
        if (w) w.textContent = `Welcome ${first}!`;
    } catch (err) {
        console.error("loadUserProfile:", err);
    }
}

// ------------------------------------------------------------
// Dashboard data
async function loadDashboardData(user) {
    try {
        const productsCol = collection(db, "products");

        // 1) Try ordered by updatedAt
        let items = [];
        try {
            const q1 = query(
                productsCol,
                where("ownerUid", "==", user.uid),
                orderBy("updatedAt", "desc")
            );
            const qs1 = await getDocs(q1);
            qs1.forEach(d => items.push({ id: d.id, ...d.data() }));
        } catch (e) {
            console.warn("updatedAt order failed, falling back:", e?.message || e);
        }

        // 2) Fallback: no orderBy (then sort client-side)
        if (items.length === 0) {
            const q2 = query(productsCol, where("ownerUid", "==", user.uid));
            const qs2 = await getDocs(q2);
            const tmp = [];
            qs2.forEach(d => tmp.push({ id: d.id, ...d.data() }));
            items = tmp.sort((a, b) => {
                const ta = (a.updatedAt?.toDate?.() || a.createdAt?.toDate?.() || 0);
                const tb = (b.updatedAt?.toDate?.() || b.createdAt?.toDate?.() || 0);
                return tb - ta;
            });
        }

        updateStats(items);
        renderRecentProducts(items.slice(0, 6));
    } catch (err) {
        console.error("loadDashboardData error:", err);
        setNotice("Error loading dashboard data", "error");
    }
}

// ------------------------------------------------------------
// Stats (simple, schema-safe)
function updateStats(products) {
    const total = products.length;
    const active = products.filter(p => (p.status || "").toLowerCase() === "ready").length;

    // mock views & rating
    const totalViews = Math.floor(Math.random() * 900) + 100;
    const avgRating = (Math.random() * 1.5 + 3.0).toFixed(1);

    $("total-products") && ($("total-products").textContent = total);
    $("total-views") && ($("total-views").textContent = totalViews.toLocaleString());
    $("avg-rating") && ($("avg-rating").textContent = avgRating);

    // sales this month: 0 for now
    const salesThisMonth = 0;
    $("sales-this-month") && ($("sales-this-month").textContent = `₹${salesThisMonth.toLocaleString()}`);
    const bar = $("sales-chart-bar");
    if (bar) bar.style.height = "5%";
}

// ------------------------------------------------------------
// Recent products grid
function renderRecentProducts(items) {
    const grid = $("recent-products-grid");
    if (!grid) return;

    if (!Array.isArray(items) || items.length === 0) {
        grid.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📦</div>
        <h3>No Products Yet</h3>
        <p>Upload your first product to get started!</p>
      </div>`;
        return;
    }

    grid.innerHTML = items.map(p => {
        const title = p.titles?.en || "untitled";
        const cat = p.category || "uncategorized";
        const desc = (p.description?.en || "");
        const price = fmtPriceRange(p.price);
        const img = firstThumb(p.media);

        return `
      <div class="product-card">
        <div class="product-image">
          <img src="${img}" alt="Product image">
        </div>
        <div class="product-info">
          <h3 class="product-name">${escapeHtml(title)}</h3>
          <span class="product-category">${escapeHtml(cat)}</span>
          <p class="product-desc">${escapeHtml(desc)}</p>
          <p class="product-price">${price}</p>
        </div>
      </div>
    `;
    }).join("");
}

// ------------------------------------------------------------
// Background video fallback (optional nicety)
document.addEventListener("DOMContentLoaded", () => {
    const video = document.querySelector(".bg-video");
    const fallback = document.querySelector(".bg-fallback");
    if (!video) return;

    video.addEventListener("error", () => {
        if (fallback) fallback.style.display = "block";
    });

    if (window.innerWidth <= 768) {
        try { video.pause(); } catch { }
    }
});

// ------------------------------------------------------------
// Logout
$("logout-btn")?.addEventListener("click", async () => {
    try {
        await signOut(auth);
        window.location.href = "/web/auth/index.html";
    } catch (err) {
        console.error("Logout error:", err);
        setNotice("Error logging out. Please try again.", "error");
    }
});
