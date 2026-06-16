const $ = (id) => document.getElementById(id);

const dropzone = $("dropzone");
const fileInput = $("fileInput");
const errorBox = $("error");
const resultCard = $("resultCard");
const loading = $("loading");

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.hidden = false;
  resultCard.hidden = true;
}

function setLoading(on) {
  loading.hidden = !on;
  if (on) {
    errorBox.hidden = true;
    resultCard.hidden = true;
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

async function predictFile(file) {
  setLoading(true);
  const localUrl = URL.createObjectURL(file);
  try {
    const form = new FormData();
    form.append("image", file);
    const res = await fetch("/api/predict", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Recognition failed.");
    render(data, localUrl);
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

// wire up events
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
