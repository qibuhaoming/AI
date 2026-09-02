const textInput = document.getElementById("text-input");
const analyzeBtn = document.getElementById("analyze-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

const sentimentEl = document.getElementById("stat-sentiment");
const wordsEl = document.getElementById("stat-words");
const sentencesEl = document.getElementById("stat-sentences");
const readingEl = document.getElementById("stat-reading");
const keywordListEl = document.getElementById("keyword-list");

async function analyze() {
  const text = textInput.value.trim();
  if (!text) {
    statusEl.textContent = "Please enter some text first.";
    return;
  }

  analyzeBtn.disabled = true;
  statusEl.textContent = "Analyzing…";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    render(data);
    statusEl.textContent = "Done.";
  } catch (error) {
    statusEl.textContent = `Error: ${error.message}`;
  } finally {
    analyzeBtn.disabled = false;
  }
}

function render(data) {
  resultsEl.hidden = false;

  sentimentEl.textContent = data.sentiment;
  sentimentEl.className = `stat__value stat__value--${data.sentiment}`;

  wordsEl.textContent = data.word_count;
  sentencesEl.textContent = data.sentence_count;
  readingEl.textContent = `${data.reading_time_seconds}s`;

  keywordListEl.innerHTML = "";
  if (data.keywords.length === 0) {
    const li = document.createElement("li");
    li.textContent = "no keywords";
    keywordListEl.appendChild(li);
    return;
  }
  for (const keyword of data.keywords) {
    const li = document.createElement("li");
    li.textContent = keyword;
    keywordListEl.appendChild(li);
  }
}

analyzeBtn.addEventListener("click", analyze);
textInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    analyze();
  }
});
