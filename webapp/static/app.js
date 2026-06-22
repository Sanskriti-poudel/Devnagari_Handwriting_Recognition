const $ = (id) => document.getElementById(id);

const dropzone = $("dropzone");
const fileInput = $("fileInput");
const errorBox = $("error");
const resultCard = $("resultCard");
const docResult = $("docResult");
const loading = $("loading");

let mode = "char"; // "char" | "doc"
const wordModel = document.body.dataset.wordModel === "true";
let lastDocId = null;   // doc_id from the latest /api/document run (needed for searchable-PDF export)

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.hidden = false;
  resultCard.hidden = true;
  docResult.hidden = true;
}

function setLoading(on) {
  loading.hidden = !on;
  $("loadingText").textContent = mode === "doc" ? "Reading document…" : "Recognizing…";
  if (on) {
    errorBox.hidden = true;
    resultCard.hidden = true;
    docResult.hidden = true;
  }
}

function render(data, inputSrc) {
  $("inputImg").src = inputSrc || data.original || data.processed;
  $("procImg").src = data.processed;
  $("glyph").textContent = data.glyph;
  $("translit").textContent = data.translit || "";
  $("className").textContent = data.class_name;

  const pct = Math.round((data.confidence || 0) * 100);
  $("confFill").style.width = pct + "%";
  $("confText").textContent = "Confidence " + pct + "%";
  $("timing").textContent = data.time_ms + " ms · CPU";

  const verdict = $("verdict");
  if ("correct" in data && data.true_glyph) {
    verdict.hidden = false;
    if (data.correct) {
      verdict.className = "verdict verdict--ok";
      verdict.textContent = "✓ Correct (true: " + data.true_glyph + ")";
    } else {
      verdict.className = "verdict verdict--bad";
      verdict.textContent = "✗ Predicted " + data.glyph + " · true: " + data.true_glyph;
    }
  } else {
    verdict.hidden = true;
  }

  resultCard.hidden = false;
  errorBox.hidden = true;
}

function renderDoc(data) {
  lastDocId = data.doc_id || null;
  $("docAnnotated").src = data.annotated;
  $("docText").value = data.text || "";
  const pct = Math.round((data.avg_confidence || 0) * 100);
  const engine = data.engine === "word-trocr" ? "Word-level TrOCR" : "CRNN (char)";
  $("docStats").textContent =
    `${engine} · ${data.num_lines} line(s) · ${data.num_chars} chars · avg conf ${pct}% · ${data.time_ms} ms · CPU`;
  // keep the note in sync with the engine that actually ran
  const isWord = data.engine === "word-trocr";
  $("docNoteWord").hidden = !isWord;
  $("docNoteChar").hidden = isWord;
  docResult.hidden = false;
  errorBox.hidden = true;
}

async function predictFile(file) {
  setLoading(true);
  // PDFs can't preview in an <img>; let render() fall back to the
  // server-rendered page (data.original / data.processed)
  const isImage = (file.type || "").startsWith("image/");
  const localUrl = isImage ? URL.createObjectURL(file) : null;
  const endpoint = mode === "doc" ? "/api/document" : "/api/predict";
  try {
    const form = new FormData();
    form.append("image", file);
    const res = await fetch(endpoint, { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Recognition failed.");
    if (mode === "doc") renderDoc(data);
    else render(data, localUrl);
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(false);
  }
}

async function predictRandom() {
  setLoading(true);
  try {
    const res = await fetch("/api/random");
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not load a sample.");
    render(data, data.original);
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(false);
  }
}

function setMode(next) {
  mode = next;
  const isDoc = next === "doc";
  $("modeDoc").classList.toggle("is-active", isDoc);
  $("modeChar").classList.toggle("is-active", !isDoc);
  $("docHint").hidden = !isDoc;
  $("charHint").hidden = isDoc;
  // before any upload, show the note for whichever engine is actually loaded
  $("docNoteWord").hidden = !(isDoc && wordModel);
  $("docNoteChar").hidden = !(isDoc && !wordModel);
  $("randomBtn").hidden = isDoc;             // random sample is char-only
  $("dropText").textContent = isDoc
    ? "Drag & drop a scanned page (image or PDF)"
    : "Drag & drop an image or PDF here";
  resultCard.hidden = true;
  docResult.hidden = true;
  errorBox.hidden = true;
}

// wire up events
$("modeChar").addEventListener("click", () => setMode("char"));
$("modeDoc").addEventListener("click", () => setMode("doc"));
$("copyBtn").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("docText").value);
    $("copyBtn").textContent = "✓ Copied";
    setTimeout(() => ($("copyBtn").textContent = "📋 Copy text"), 1500);
  } catch (_e) {
    $("docText").select();
  }
});
$("browseBtn").addEventListener("click", () => fileInput.click());
$("randomBtn").addEventListener("click", predictRandom);
fileInput.addEventListener("change", (e) => {
  if (e.target.files[0]) predictFile(e.target.files[0]);
});

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("is-drag");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("is-drag");
  })
);
dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) predictFile(file);
});

// ---------------------------------------------------------------- export
// Download the (possibly edited) recognized text as txt | docx | searchable pdf.
async function exportAs(fmt, btn) {
  const text = $("docText").value;
  if (!text.trim() && fmt !== "pdf") {
    showError("Nothing to export yet — run a document scan first.");
    return;
  }
  const body = { format: fmt, text };
  if (fmt === "pdf") {
    if (!lastDocId) {
      showError("Searchable PDF needs the original scan — re-run the document, then export.");
      return;
    }
    body.doc_id = lastDocId;
  }
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = "…";
  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Export failed.");
    }
    const blob = await res.blob();
    const ext = fmt === "pdf" ? "pdf" : fmt === "docx" ? "docx" : "txt";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "recognized." + ext;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    showError(e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

$("exportTxt").addEventListener("click", (e) => exportAs("txt", e.currentTarget));
$("exportDocx").addEventListener("click", (e) => exportAs("docx", e.currentTarget));
$("exportPdf").addEventListener("click", (e) => exportAs("pdf", e.currentTarget));

// ------------------------------------------------------- romanized typing
// When enabled, transliterate each Latin "word" to Devanagari as the user
// presses space / enter (e.g. "namaste " -> "नमस्ते "). Powered by translit.js.
let romanOn = false;
$("romanToggle").addEventListener("change", (e) => {
  romanOn = e.target.checked;
  $("romanHint").hidden = !romanOn;
});

function attachRomanizedTyping(el) {
  el.addEventListener("keydown", (e) => {
    if (!romanOn || (e.key !== " " && e.key !== "Enter")) return;
    if (el.selectionStart !== el.selectionEnd) return;       // active selection: leave alone
    if (typeof window.romanToDevanagari !== "function") return;
    const pos = el.selectionStart;
    const m = el.value.slice(0, pos).match(/([A-Za-z]+)$/);  // the word just typed
    if (!m) return;
    const token = m[1];
    const dev = window.romanToDevanagari(token);
    if (dev === token) return;                               // nothing to convert
    e.preventDefault();
    const sep = e.key === "Enter" ? "\n" : " ";
    const start = pos - token.length;
    el.value = el.value.slice(0, start) + dev + sep + el.value.slice(pos);
    const caret = start + dev.length + sep.length;
    el.selectionStart = el.selectionEnd = caret;
  });
}
attachRomanizedTyping($("docText"));

// --------------------------------------------------------- Preeti tools
// Live Preeti <-> Unicode conversion (preeti.js). Default Preeti -> Unicode.
let preetiDir = "p2u"; // "p2u" | "u2p"
const preetiIn = $("preetiIn");
const preetiOut = $("preetiOut");

function runPreeti() {
  const src = preetiIn.value;
  if (preetiDir === "p2u") {
    preetiOut.value = window.preetiToUnicode ? window.preetiToUnicode(src) : src;
  } else {
    preetiOut.value = window.unicodeToPreeti ? window.unicodeToPreeti(src) : src;
  }
}

function setPreetiDir(dir) {
  preetiDir = dir;
  const p2u = dir === "p2u";
  $("dirP2U").classList.toggle("is-active", p2u);
  $("dirU2P").classList.toggle("is-active", !p2u);
  $("preetiInLabel").textContent = p2u ? "Preeti text (paste here)" : "Unicode text (paste here)";
  $("preetiOutLabel").textContent = p2u ? "Unicode" : "Preeti";
  // the Preeti side is raw Latin keystrokes — show it in a monospace font
  preetiIn.classList.toggle("doctext--mono", p2u);
  preetiOut.classList.toggle("doctext--mono", !p2u);
  preetiIn.placeholder = p2u ? "Paste Preeti-encoded text, e.g.  g]kfn" : "नेपाली युनिकोड यहाँ पेस्ट गर्नुहोस्";
  runPreeti();
}

preetiIn.addEventListener("input", runPreeti);
$("dirP2U").addEventListener("click", () => setPreetiDir("p2u"));
$("dirU2P").addEventListener("click", () => setPreetiDir("u2p"));
$("preetiCopy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(preetiOut.value);
    $("preetiCopy").textContent = "✓ Copied";
    setTimeout(() => ($("preetiCopy").textContent = "📋 Copy"), 1500);
  } catch (_e) {
    preetiOut.select();
  }
});
$("preetiSwap").addEventListener("click", () => {
  preetiIn.value = preetiOut.value;
  setPreetiDir(preetiDir === "p2u" ? "u2p" : "p2u");
});
