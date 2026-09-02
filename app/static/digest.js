const runBtn = document.getElementById("run-btn");
const interestsInput = document.getElementById("interests-input");
const minEngagementInput = document.getElementById("min-engagement");
const langSelect = document.getElementById("lang-select");
const urlInput = document.getElementById("url-input");
const statusEl = document.getElementById("status");

const postsPanel = document.getElementById("posts-panel");
const postCountEl = document.getElementById("post-count");
const postListEl = document.getElementById("post-list");

const methodologyPanel = document.getElementById("methodology-panel");
const methodologyEl = document.getElementById("methodology");

function renderMarkdown(md) {
  // Minimal renderer: headings, blockquotes, list items, bold, and paragraphs.
  const escape = (s) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  const bold = (s) => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  const html = [];
  for (const raw of md.split("\n")) {
    const line = raw.trimEnd();
    if (!line) continue;
    if (line.startsWith("### ")) html.push(`<h3>${bold(escape(line.slice(4)))}</h3>`);
    else if (line.startsWith("## ")) html.push(`<h2>${bold(escape(line.slice(3)))}</h2>`);
    else if (line.startsWith("# ")) html.push(`<h1>${bold(escape(line.slice(2)))}</h1>`);
    else if (line.startsWith("> ")) html.push(`<blockquote>${bold(escape(line.slice(2)))}</blockquote>`);
    else if (/^\d+\.\s/.test(line)) html.push(`<li>${bold(escape(line.replace(/^\d+\.\s/, "")))}</li>`);
    else if (line.startsWith("- ")) html.push(`<li>${bold(escape(line.slice(2)))}</li>`);
    else html.push(`<p>${bold(escape(line))}</p>`);
  }
  return html.join("\n");
}

async function buildDigest() {
  const interests = interestsInput.value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const minEngagement = Number(minEngagementInput.value) || 0;
  const lang = langSelect ? langSelect.value : "auto";
  const url = urlInput && urlInput.value.trim() ? urlInput.value.trim() : null;

  runBtn.disabled = true;
  statusEl.textContent = "Building digest…";

  try {
    const response = await fetch("/api/digest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        interests,
        min_engagement: minEngagement,
        lang,
        url,
      }),
    });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    const data = await response.json();
    render(data);
    statusEl.textContent = `Fetched ${data.fetched}, selected ${data.selected.length}.`;
  } catch (error) {
    statusEl.textContent = `Error: ${error.message}`;
  } finally {
    runBtn.disabled = false;
  }
}

function render(data) {
  postsPanel.hidden = false;
  methodologyPanel.hidden = false;

  postCountEl.textContent = data.selected.length;
  postListEl.innerHTML = "";
  for (const post of data.selected) {
    const li = document.createElement("li");
    li.className = "post";

    const badge = post.is_article
      ? '<span class="tag tag--article">article</span>'
      : "";
    const kw = post.matched_keywords.length
      ? `<div class="post__kw">interests: ${post.matched_keywords.join(", ")}</div>`
      : "";

    li.innerHTML = `
      <div class="post__head">
        <span class="post__author">${post.author}</span>
        ${badge}
        <span class="post__score">score ${post.score}</span>
      </div>
      ${post.title ? `<div class="post__title">${post.title}</div>` : ""}
      <div class="post__text">${post.text}</div>
      ${kw}
      <div class="post__meta">${post.engagement} engagement</div>
    `;
    postListEl.appendChild(li);
  }

  methodologyEl.innerHTML = renderMarkdown(data.methodology_markdown);
}

function applyQueryParams() {
  const params = new URLSearchParams(window.location.search);
  const interests = params.get("interests");
  if (interests) interestsInput.value = interests;
  const lang = params.get("lang");
  if (lang && langSelect) {
    const allowed = ["auto", "en", "zh"];
    if (allowed.includes(lang)) langSelect.value = lang;
  }
  const minEngagement = params.get("min_engagement");
  if (minEngagement !== null) minEngagementInput.value = minEngagement;
  const url = params.get("url");
  if (url && urlInput) urlInput.value = url;
}

applyQueryParams();

runBtn.addEventListener("click", buildDigest);
