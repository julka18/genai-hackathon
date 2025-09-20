// web/products/app.js  (NO <script> TAGS HERE)

// ---------------------- Firebase (CDN) ----------------------
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
    getAuth, onAuthStateChanged, signOut
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import {
    arrayUnion,
    collection,
    deleteDoc,
    doc,
    getDoc,
    getFirestore,
    onSnapshot,
    orderBy,
    query,
    serverTimestamp,
    updateDoc,
    where
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

// ---------------------- Config ----------------------
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

// ---------------------- DOM helpers ----------------------
const $ = (sel) => document.querySelector(sel);
const grid = $("#products-grid");
const emptyState = $("#empty-state");
const totalEl = $("#total-products-count");
const activeEl = $("#active-products-count");
const draftEl = $("#draft-products-count");
const logoutBtn = $("#logout-btn");

// Edit modal els
const modal = $("#edit-modal");
const modalClose = $("#modal-close");
const cancelEditBtn = $("#cancel-edit");
const editForm = $("#edit-form");
const nameInp = $("#edit-productName");
const catInp = $("#edit-category");
const descInp = $("#edit-description");
const priceInp = $("#edit-price");
const qtyInp = $("#edit-quantity");
const currentImages = $("#current-images");
const uploadArea = $("#edit-upload-area");
const imageInput = $("#edit-image-input");
const newPreview = $("#edit-image-preview");

let CURRENT_USER = null;
let CURRENT_EDIT_ID = null;
let NEW_IMAGES = []; // base64 strings to append

// ---------------------- Auth guard ----------------------
onAuthStateChanged(auth, async (user) => {
    if (!user) {
        window.location.href = "/web/auth/index.html";
        return;
    }
    CURRENT_USER = user;
    const welcome = $(".welcome-text");
    if (welcome) welcome.textContent = "Welcome " + (user.displayName || "artisan") + "!";
    startProductsListener();
});

logoutBtn?.addEventListener("click", () => signOut(auth));

// ---------------------- Live products feed ----------------------
function startProductsListener() {
    const q = query(
        collection(db, "products"),
        where("ownerUid", "==", CURRENT_USER.uid),
        orderBy("updatedAt", "desc") // equality + orderBy is OK without composite index
    );

    onSnapshot(q, (snap) => {
        const items = [];
        snap.forEach((d) => items.push({ id: d.id, ...d.data() }));

        // Counters
        totalEl.textContent = items.length;
        activeEl.textContent = items.filter((p) => p.status === "ready").length;
        draftEl.textContent = items.filter((p) => p.status !== "ready").length;

        // Render
        if (items.length === 0) {
            grid.innerHTML = "";
            emptyState.style.display = "block";
        } else {
            emptyState.style.display = "none";
            grid.innerHTML = items.map(renderCard).join("");
        }

        // Attach handlers
        grid.querySelectorAll("[data-edit]").forEach(btn => {
            btn.addEventListener("click", () => openEdit(btn.dataset.edit));
        });
        grid.querySelectorAll("[data-delete]").forEach(btn => {
            btn.addEventListener("click", () => deleteProduct(btn.dataset.delete));
        });
    }, (err) => {
        console.error("products feed error:", err);
    });
}

// ---------------------- Card renderer ----------------------
function renderCard(p) {
    const title = p.titles?.en || "untitled";
    const category = p.category || "uncategorized";
    const desc = (p.description?.en || "").toString();
    const priceText = p.price ? `₹${p.price.low ?? "-"} – ₹${p.price.high ?? "-"}` : "No price";
    const status = p.status || "draft";

    let thumb = "/web/auth/placeholder.png";
    if (Array.isArray(p.media) && p.media.length) {
        const first = p.media[0];
        if (first.base64) thumb = `data:image/jpeg;base64,${first.base64}`;
        if (first.url) thumb = first.url;
    }

    return `
      <div class="product-card">
        <div class="product-thumb">
          <img alt="${escapeHtml(title)}" src="${thumb}">
          <span class="badge ${status === "ready" ? "ok" : "muted"}">${status}</span>
        </div>
        <div class="product-body">
          <h3 class="product-title">${escapeHtml(title)}</h3>
          <div class="product-cat">${escapeHtml(category)}</div>
          <div class="product-desc">${escapeHtml(desc)}</div>
          <div class="product-price">${priceText}</div>
        </div>
        <div class="product-actions">
          <button class="btn small" data-edit="${p.id}">✏️ Edit</button>
          <button class="btn small danger" data-delete="${p.id}">🗑 Delete</button>
        </div>
      </div>
    `;
}


function escapeHtml(s) {
    return (s ?? "").toString().replace(/[&<>"']/g, m => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    })[m]);
}

// ---------------------- Edit flow ----------------------
async function openEdit(docId) {
    CURRENT_EDIT_ID = docId;
    NEW_IMAGES = [];
    newPreview.innerHTML = "";
    if (imageInput) imageInput.value = "";

    const ref = doc(db, "products", docId);
    const snap = await getDoc(ref);
    if (!snap.exists()) return;

    const p = snap.data();

    // Populate fields (upload step used min/max; modal has single price)
    nameInp.value = p.titles?.en || "";
    catInp.value = p.category || "";
    descInp.value = p.description?.en || "";
    priceInp.value = p.price?.high ?? p.price?.low ?? "";

    // Qty optional
    qtyInp.value = p.quantity ?? 1;

    // Current images
    currentImages.innerHTML = renderExistingImages(p.media);

    // open modal
    modal.classList.add("open");
}

function renderExistingImages(mediaArr) {
    if (!Array.isArray(mediaArr) || mediaArr.length === 0) {
        return `<div class="muted">No images yet</div>`;
    }
    return `
    <div class="image-list">
      ${mediaArr.map((m, i) => {
        const src = m?.base64 ? `data:image/jpeg;base64,${m.base64}` : (m?.url || "/web/auth/placeholder.png");
        return `
          <div class="image-chip">
            <img src="${src}" alt="img ${i}">
            <span class="muted">#${m?.order ?? i}</span>
          </div>
        `;
    }).join("")}
    </div>
  `;
}

// Close modal
modalClose?.addEventListener("click", () => modal.classList.remove("open"));
cancelEditBtn?.addEventListener("click", () => modal.classList.remove("open"));

// Upload area -> trigger input
uploadArea?.addEventListener("click", () => imageInput?.click());

// File -> base64
imageInput?.addEventListener("change", async (e) => {
    const files = Array.from(e.target.files || []);
    for (const f of files.slice(0, 5)) {
        const b64 = await fileToBase64(f);
        NEW_IMAGES.push({ base64: b64, type: "image" });
        newPreview.insertAdjacentHTML("beforeend", `
      <div class="image-chip">
        <img src="data:image/jpeg;base64,${b64}">
        <span class="muted">new</span>
      </div>
    `);
    }
});

// Save Changes
editForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!CURRENT_EDIT_ID) return;

    const ref = doc(db, "products", CURRENT_EDIT_ID);
    const snap = await getDoc(ref);
    if (!snap.exists()) return;

    const p = snap.data();
    const nextOrderStart = Array.isArray(p.media) ? p.media.length : 0;

    // Build updates
    const update = {
        titles: { en: nameInp.value.trim(), hi: p.titles?.hi ?? "" },
        category: catInp.value,
        description: { en: descInp.value.trim(), hi: p.description?.hi ?? "" },
        price: {
            low: Number(priceInp.value) || 0,
            high: Number(priceInp.value) || 0,
            currency: p.price?.currency || "INR"
        },
        updatedAt: serverTimestamp()
    };

    await updateDoc(ref, update);

    // Append new images (arrayUnion one-by-one with order)
    let order = nextOrderStart;
    for (const n of NEW_IMAGES) {
        await updateDoc(ref, {
            media: arrayUnion({ type: "image", base64: n.base64, order })
        });
        order += 1;
    }

    // Done
    modal.classList.remove("open");
});

// Delete product
async function deleteProduct(id) {
    if (!confirm("Delete this product?")) return;
    await deleteDoc(doc(db, "products", id));
}

// ---------------------- utils ----------------------
function fileToBase64(file) {
    return new Promise((res, rej) => {
        const reader = new FileReader();
        reader.onload = () => {
            // reader.result is "data:<mime>;base64,<payload>"
            const uri = reader.result;
            const base64 = (uri.split(",")[1]) || "";
            res(base64);
        };
        reader.onerror = rej;
        reader.readAsDataURL(file);
    });
}
