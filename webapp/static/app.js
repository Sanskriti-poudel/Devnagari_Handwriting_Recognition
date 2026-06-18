const $ = (id) => document.getElementById(id);

const dropzone = $("dropzone");
const fileInput = $("fileInput");
const errorBox = $("error");
const resultCard = $("resultCard");
const docResult = $("docResult");
const loading = $("loading");

let mode = "char"; // "char" | "doc"
const wordModel = document.body.dataset.wordModel === "true";

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
