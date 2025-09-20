// /web/upload/photos.js
// Two-step UI:
//  - Step 1: images + Back / Next
//  - Step 2: "Generate AI Ads & Post..." OR "Post..." -> shows "yaha se julka ka kaam"

// ---- helpers ----
const $ = (sel) => document.querySelector(sel);
const notice = $("#notice");
function setNotice(msg, ok = false) { if (!notice) return; notice.textContent = msg; notice.style.color = ok ? "#A7F3D0" : "#bbb"; }
function showToast(text) {
    const t = $("#toast");
    if (!t) { alert(text); return; }
    t.textContent = text;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 1400);
}
function getQuery(key) {
    const url = new URL(window.location.href);
    return url.searchParams.get(key);
}

// ---- elements ----
const drop = $("#drop");
const fileInput = $("#file-input");
const chooseBtn = $("#choose-files");
const thumbs = $("#thumbs");
const backBtn = $("#btn-back");
const nextBtn = $("#btn-next");
const step2 = $("#step2");
const aiAndPostBtn = $("#btn-ai-and-post");
const postOnlyBtn = $("#btn-post-only");

// maintain picked files locally (convert to base64 on save, if you already have that logic)
let pickedFiles = [];

// ---- wire Back link to details step using pid ----
const pid = getQuery("pid");
backBtn.href = `/web/upload/index.html${pid ? `?pid=${encodeURIComponent(pid)}` : ""}`;

// ---- basic UI wiring (doesn't touch your Firestore write code) ----
chooseBtn?.addEventListener("click", () => fileInput.click());
drop?.addEventListener("click", (e) => { if (e.target === drop) fileInput.click(); });

drop?.addEventListener("dragover", (e) => {
    e.preventDefault(); drop.style.borderColor = "rgba(255,255,255,.35)";
});
drop?.addEventListener("dragleave", () => {
    drop.style.borderColor = "rgba(255,255,255,.15)";
});
drop?.addEventListener("drop", (e) => {
    e.preventDefault();
    drop.style.borderColor = "rgba(255,255,255,.15)";
    handleFiles(e.dataTransfer.files);
});

fileInput?.addEventListener("change", (e) => handleFiles(e.target.files));

function handleFiles(fileList) {
    const files = Array.from(fileList || []);
    const room = Math.max(0, 5 - pickedFiles.length);
    const slice = files.slice(0, room);
    if (!slice.length) return;
    pickedFiles.push(...slice);
    renderThumbs();
}

function renderThumbs() {
    thumbs.innerHTML = pickedFiles.map((f, i) => `
    <div class="thumb">
      <img id="img-${i}" alt="preview">
      <span class="tag">${i === 0 ? "main" : `#${i}`}</span>
    </div>
  `).join("");

    // object URLs for instant preview
    pickedFiles.forEach((file, i) => {
        const img = document.getElementById(`img-${i}`);
        if (!img) return;
        img.src = URL.createObjectURL(file);
        img.onload = () => URL.revokeObjectURL(img.src);
    });
}

// ---- NEXT: save (placeholder) then reveal step 2 ----
nextBtn?.addEventListener("click", async () => {
    // If you already have Firestore save code, call it here.
    if (pickedFiles.length === 0) {
        setNotice("Please add at least one image.");
        return;
    }

    setNotice("Saving photos…");
    await new Promise(r => setTimeout(r, 600)); // simulate
    setNotice("✅ Photos saved.", true);

    // show step-2 CTAs
    step2.style.display = "block";
    // scroll to the CTAs
    step2.scrollIntoView({ behavior: "smooth", block: "start" });
});

// ---- Step-2 CTAs -> show the required message ----
aiAndPostBtn?.addEventListener("click", () => {
    showToast("yaha se julka ka kaam");
});

postOnlyBtn?.addEventListener("click", () => {
    showToast("yaha se julka ka kaam");
});
