const state = {
  posts: [],
  filter: "all",
  query: "",
};

const categoryLabels = {
  announcements: "ANNOUNCE",
  syntax: "LANGUAGE",
  ide: "TOOLCHAIN",
  showcase: "SHOWCASE",
  help: "HELP",
  general: "GENERAL",
};

const categoryClass = {
  announcements: "is-yellow",
  syntax: "is-red",
  ide: "is-blue",
  showcase: "is-green",
  help: "is-purple",
  general: "is-ink",
};

const categoryIcons = {
  announcements: "icon-spark",
  syntax: "icon-code",
  ide: "icon-monitor",
  showcase: "icon-spark",
  help: "icon-help",
  general: "icon-grid",
};

const els = {
  threadCount: document.querySelector("#threadCount"),
  replyCount: document.querySelector("#replyCount"),
  signalCount: document.querySelector("#signalCount"),
  postList: document.querySelector("#postList"),
  composerCard: document.querySelector("#composerCard"),
  postForm: document.querySelector("#postForm"),
  searchInput: document.querySelector("#searchInput"),
  seedDemo: document.querySelector("#seedDemo"),
  refreshPosts: document.querySelector("#refreshPosts"),
  focusComposer: document.querySelector("#focusComposer"),
  navFilters: Array.from(document.querySelectorAll(".nav-filter")),
  message: document.querySelector("#message"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with ${response.status}`);
  }
  return payload;
}

async function loadPosts({ seedWhenEmpty = true } = {}) {
  const payload = await api("/api/forum/posts");
  state.posts = payload.posts || [];

  if (state.posts.length === 0 && seedWhenEmpty) {
    const seeded = await api("/api/forum/posts/demo", { method: "POST", body: "{}" });
    state.posts = seeded.posts || [];
  }

  render();
}

function visiblePosts() {
  const query = state.query.trim().toLowerCase();
  return state.posts.filter((post) => {
    const matchesFilter = state.filter === "all" || post.category === state.filter;
    if (!matchesFilter) return false;
    if (!query) return true;
    const haystack = [
      post.title,
      post.body,
      post.author,
      post.category,
      ...(post.tags || []),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

function render() {
  renderStats();
  renderFilters();
  renderPostList();
}

function renderStats() {
  const replies = state.posts.reduce((total, post) => total + (post.comments?.length || 0), 0);
  const signals = state.posts.reduce((total, post) => total + Number(post.reactions || 0), 0);
  if (els.threadCount) els.threadCount.textContent = String(state.posts.length);
  if (els.replyCount) els.replyCount.textContent = String(replies);
  if (els.signalCount) els.signalCount.textContent = String(signals);
}

function renderFilters() {
  for (const button of els.navFilters) {
    button.classList.toggle("is-active", button.dataset.filter === state.filter);
  }
}

function renderPostList() {
  const posts = visiblePosts();
  if (posts.length === 0) {
    els.postList.replaceChildren(emptyState("icon-help", "无匹配"));
    return;
  }
  els.postList.replaceChildren(...posts.map(renderPostCard));
}

function renderPostCard(post) {
  const card = document.createElement("article");
  card.className = "post-card";
  card.dataset.href = postHref(post.id);
  card.addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    window.location.href = card.dataset.href;
  });

  const top = document.createElement("div");
  top.className = "post-topline";
  const category = categoryPill(post.category);
  const meta = iconMeta("icon-user", `${post.author} / ${relativeTime(post.updated_at || post.created_at)}`);
  top.append(category, meta);

  const title = document.createElement("a");
  title.className = "post-title-button";
  title.href = postHref(post.id);
  if (post.pinned) {
    title.append(icon("icon-spark"), document.createTextNode(post.title));
  } else {
    title.textContent = post.title;
  }

  const tagRow = document.createElement("div");
  tagRow.className = "tag-row";
  for (const tag of (post.tags || []).slice(0, 3)) {
    const item = document.createElement("span");
    item.append(icon("icon-tag"), document.createTextNode(tag));
    tagRow.append(item);
  }

  const stats = document.createElement("div");
  stats.className = "post-stats";
  stats.append(
    statChip("icon-message", post.comments?.length || 0, "Replies"),
    statChip("icon-signal", post.reactions || 0, "Signals"),
    statChip("icon-eye", post.views || 1, "Views"),
  );

  card.append(top, title, tagRow, stats);
  return card;
}

function statChip(iconName, value, label) {
  const chip = document.createElement("span");
  chip.className = "stat-chip";
  chip.title = label;
  chip.setAttribute("aria-label", `${label}: ${value}`);
  chip.append(icon(iconName));
  const number = document.createElement("strong");
  number.textContent = String(value);
  chip.append(number);
  return chip;
}

function emptyState(iconName, text) {
  const wrapper = document.createElement("div");
  wrapper.className = "empty-state";
  wrapper.append(icon(iconName));
  const copy = document.createElement("span");
  copy.textContent = text;
  wrapper.append(copy);
  return wrapper;
}

function categoryPill(category) {
  const label = categoryLabels[category] || category;
  const pill = document.createElement("span");
  pill.className = `category-pill ${categoryClass[category] || "is-ink"}`;
  pill.title = label;
  pill.setAttribute("aria-label", label);
  const text = document.createElement("span");
  text.textContent = label;
  pill.append(icon(categoryIcons[category] || "icon-grid"), text);
  return pill;
}

function iconMeta(iconName, text) {
  const meta = document.createElement("span");
  meta.className = "icon-meta";
  meta.append(icon(iconName), document.createTextNode(text));
  return meta;
}

function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.classList.add("icon");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `#${name}`);
  svg.append(use);
  return svg;
}

function readPostForm(form) {
  const data = new FormData(form);
  return {
    author: String(data.get("author") || ""),
    title: String(data.get("title") || ""),
    category: String(data.get("category") || "general"),
    tags: splitTags(String(data.get("tags") || "")),
    body: String(data.get("body") || ""),
  };
}

function splitTags(value) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 5);
}

async function createPost(event) {
  event.preventDefault();
  try {
    const payload = await api("/api/forum/posts", {
      method: "POST",
      body: JSON.stringify(readPostForm(els.postForm)),
    });
    window.location.href = postHref(payload.post.id);
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function seedBoard() {
  try {
    const payload = await api("/api/forum/posts/demo", { method: "POST", body: "{}" });
    state.posts = payload.posts || [];
    render();
    setMessage("已载入");
  } catch (error) {
    setMessage(error.message, true);
  }
}

function setFilter(filter) {
  state.filter = filter;
  render();
}

function setMessage(text, isError = false) {
  els.message.textContent = text;
  els.message.className = isError ? "message is-error" : "message";
}

function postHref(postId) {
  return `/posts/${encodeURIComponent(postId)}`;
}

function relativeTime(value) {
  if (!value) return "now";
  const then = new Date(value).getTime();
  if (!Number.isFinite(then)) return "now";
  const seconds = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (seconds < 60) return "now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

els.navFilters.forEach((button) => {
  button.addEventListener("click", () => setFilter(button.dataset.filter || "all"));
});
els.searchInput.addEventListener("input", () => {
  state.query = els.searchInput.value;
  renderPostList();
});
els.seedDemo.addEventListener("click", seedBoard);
els.refreshPosts.addEventListener("click", () => loadPosts({ seedWhenEmpty: false }));
els.focusComposer.addEventListener("click", () => {
  els.composerCard.scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => els.postForm.elements.title.focus(), 280);
});
els.postForm.addEventListener("submit", createPost);

loadPosts().catch((error) => setMessage(error.message, true));
