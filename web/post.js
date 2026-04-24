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

const state = {
  post: null,
  postId: postIdFromLocation(),
};

const els = {
  postDetail: document.querySelector("#postDetail"),
  replyList: document.querySelector("#replyList"),
  replyForm: document.querySelector("#replyForm"),
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

async function loadPost() {
  if (!state.postId) {
    throw new Error("missing post id");
  }
  const payload = await api(`/api/forum/posts/${encodeURIComponent(state.postId)}`);
  state.post = payload.post;
  render();
}

function render() {
  if (!state.post) return;
  document.title = `${state.post.title} / Styio Community`;
  renderPostDetail();
  renderReplies();
}

function renderPostDetail() {
  const post = state.post;
  const wrapper = document.createElement("div");
  wrapper.className = "thread-detail";

  const header = document.createElement("div");
  header.className = "detail-header";
  header.append(
    categoryPill(post.category),
    iconMeta("icon-user", `${post.author} / ${formatDate(post.created_at)}`),
  );

  const title = document.createElement("h1");
  title.textContent = post.title;

  const body = document.createElement("p");
  body.className = "thread-body";
  body.textContent = post.body;

  const tagRow = document.createElement("div");
  tagRow.className = "tag-row";
  for (const tag of post.tags || []) {
    const item = document.createElement("span");
    item.append(icon("icon-tag"), document.createTextNode(tag));
    tagRow.append(item);
  }

  const actionRow = document.createElement("div");
  actionRow.className = "thread-actions";
  const react = document.createElement("button");
  react.className = "toon-button is-yellow";
  react.type = "button";
  react.append(icon("icon-signal"), textSpan(String(post.reactions || 0)));
  react.addEventListener("click", reactToPost);
  const stats = document.createElement("div");
  stats.className = "post-stats";
  stats.append(
    statChip("icon-message", post.comments?.length || 0, "Replies"),
    statChip("icon-eye", post.views || 1, "Views"),
  );
  actionRow.append(react, stats);

  wrapper.append(header, title, body, tagRow, actionRow);
  els.postDetail.replaceChildren(wrapper);
}

function renderReplies() {
  const replies = state.post?.comments || [];
  if (replies.length === 0) {
    const empty = document.createElement("li");
    empty.className = "reply-empty";
    empty.append(icon("icon-message"), document.createTextNode("0"));
    els.replyList.replaceChildren(empty);
    return;
  }
  els.replyList.replaceChildren(...replies.map(renderReply));
}

function renderReply(comment) {
  const item = document.createElement("li");
  const head = document.createElement("div");
  head.className = "reply-head";
  const author = document.createElement("strong");
  author.append(icon("icon-user"), document.createTextNode(comment.author));
  const time = iconMeta("icon-send", relativeTime(comment.created_at));
  head.append(author, time);

  const body = document.createElement("p");
  body.textContent = comment.body;
  item.append(head, body);
  return item;
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

function categoryPill(category) {
  const label = categoryLabels[category] || category;
  const pill = document.createElement("span");
  pill.className = `category-pill ${categoryClass[category] || "is-ink"}`;
  pill.title = label;
  pill.setAttribute("aria-label", label);
  pill.append(icon(categoryIcons[category] || "icon-grid"), textSpan(label));
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

function textSpan(text) {
  const span = document.createElement("span");
  span.textContent = text;
  return span;
}

async function createReply(event) {
  event.preventDefault();
  const data = new FormData(els.replyForm);
  try {
    const payload = await api(`/api/forum/posts/${encodeURIComponent(state.postId)}/comments`, {
      method: "POST",
      body: JSON.stringify({
        author: String(data.get("author") || ""),
        body: String(data.get("body") || ""),
      }),
    });
    els.replyForm.elements.body.value = "";
    state.post = payload.post;
    render();
    setMessage("已发送");
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function reactToPost() {
  try {
    const payload = await api(`/api/forum/posts/${encodeURIComponent(state.postId)}/react`, {
      method: "POST",
      body: "{}",
    });
    state.post = payload.post;
    render();
    setMessage("+1");
  } catch (error) {
    setMessage(error.message, true);
  }
}

function setMessage(text, isError = false) {
  els.message.textContent = text;
  els.message.className = isError ? "message is-error" : "message";
}

function postIdFromLocation() {
  const match = window.location.pathname.match(/^\/posts\/([^/]+)\/?$/);
  if (match) return decodeURIComponent(match[1]);
  return new URLSearchParams(window.location.search).get("id");
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

function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

els.replyForm.addEventListener("submit", createReply);
loadPost().catch((error) => {
  els.postDetail.replaceChildren();
  els.replyForm.hidden = true;
  setMessage(error.message, true);
});
