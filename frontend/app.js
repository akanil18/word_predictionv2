async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return await res.json();
}

function setStatus(msg, isError = false) {
  const el = document.getElementById("status");
  el.textContent = msg || "";
  el.classList.toggle("error", !!isError);
}

function renderSuggestions(words) {
  const wrap = document.getElementById("suggestions");
  wrap.innerHTML = "";

  if (!words || words.length === 0) {
    wrap.textContent = "—";
    return;
  }

  for (const w of words) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = w;
    chip.title = "Click to append";
    chip.style.cursor = "pointer";
    chip.addEventListener("click", () => {
      const ta = document.getElementById("textInput");
      const current = ta.value.trimEnd();
      ta.value = current.length ? `${current} ${w}` : w;
      ta.focus();
    });
    wrap.appendChild(chip);
  }
}

async function predict() {
  const btn = document.getElementById("predictBtn");
  const text = document.getElementById("textInput").value;
  const apiBase = document.getElementById("apiBase").value.trim().replace(/\/$/, "");
  const k = Number(document.getElementById("kInput").value || 1);

  if (!apiBase) {
    setStatus("Please set the API base URL.", true);
    return;
  }

  btn.disabled = true;
  setStatus("Predicting…");

  try {
    const data = await postJson(`${apiBase}/predict`, { text, k });

    document.getElementById("nextWord").textContent = data.next_word ?? "—";
    renderSuggestions(data.suggestions ?? []);
    setStatus("Done.");
  } catch (err) {
    document.getElementById("nextWord").textContent = "—";
    renderSuggestions([]);
    setStatus(err?.message || String(err), true);
  } finally {
    btn.disabled = false;
  }
}

function clearAll() {
  document.getElementById("textInput").value = "";
  document.getElementById("nextWord").textContent = "—";
  renderSuggestions([]);
  setStatus("");
}

document.getElementById("predictBtn").addEventListener("click", predict);
document.getElementById("clearBtn").addEventListener("click", clearAll);

// Ctrl+Enter to predict
document.getElementById("textInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    predict();
  }
});
