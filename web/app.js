import {
  authorTimestamp,
  bindUserFieldColor,
  categoryClass,
  categoryIcons,
  categorySelectField,
  emptyState,
  iconField,
  iconTitle,
  postFooter,
  postPreview,
  readPostForm,
  relativeTime,
  tagsField,
  textAreaField,
  userField,
} from "./components.js";

const state = {
  posts: [],
  filter: "all",
  query: "",
};

const els = {
  threadCount: document.querySelector("#threadCount"),
  replyCount: document.querySelector("#replyCount"),
  signalCount: document.querySelector("#signalCount"),
  postList: document.querySelector("#postList"),
  composerCard: document.querySelector("#composerCard"),
  postForm: document.querySelector("#postForm"),
  postAuthorSlot: document.querySelector("#postAuthorSlot"),
  postTitleSlot: document.querySelector("#postTitleSlot"),
  postBodySlot: document.querySelector("#postBodySlot"),
  postCategorySlot: document.querySelector("#postCategorySlot"),
  postTagsSlot: document.querySelector("#postTagsSlot"),
  searchInput: document.querySelector("#searchInput"),
  refreshPosts: document.querySelector("#refreshPosts"),
  focusComposer: document.querySelector("#focusComposer"),
  navFilters: Array.from(document.querySelectorAll(".nav-filter")),
  message: document.querySelector("#message"),
};

mountPostComposerFields();

async function api(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
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

function mountPostComposerFields() {
  const authorField = userField({
    className: "composer-author-field",
    form: "postForm",
    autocomplete: "name",
  });
  els.postAuthorSlot?.replaceChildren(authorField);
  bindUserFieldColor(authorField);

  els.postTitleSlot?.replaceChildren(
    iconField({
      className: "title-field",
      iconName: "icon-title",
      name: "title",
      maxLength: 120,
      required: true,
      placeholder: "一句话说明讨论主题",
    }),
  );
  els.postBodySlot?.replaceChildren(
    textAreaField({
      className: "body-field",
      name: "body",
      rows: 6,
      maxLength: 4000,
      required: true,
      placeholder: "贴出背景、例子、问题或建议。",
    }),
  );
  els.postCategorySlot?.replaceChildren(categorySelectField());
  els.postTagsSlot?.replaceChildren(tagsField({ placeholder: "parser, adapter, snippets" }));
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
  const activeFilter = state.filter === "all" ? "" : state.filter;
  for (const button of els.navFilters) {
    button.classList.toggle("is-active", button.dataset.filter === activeFilter);
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
  card.className = ["post-card", categoryClass[post.category] || "is-ink"].join(" ");
  card.dataset.href = postHref(post.id);
  card.addEventListener("click", (event) => {
    if (event.target.closest("a, button")) return;
    window.location.href = card.dataset.href;
  });

  const title = iconTitle({
    className: "post-title-button",
    href: postHref(post.id),
    text: post.title,
    iconName: post.pinned ? "icon-pin" : categoryIcons[post.category] || "icon-grid",
    markerClassName: post.pinned ? "is-pinned" : "is-category",
    markerLabel: post.pinned ? "Pinned" : "Category",
  });

  const header = document.createElement("div");
  header.className = "post-card-header";
  header.append(
    title,
    authorTimestamp({ author: post.author, timestamp: post.updated_at || post.created_at, format: relativeTime }),
  );

  card.append(
    header,
    postPreview(post),
    postFooter(post, { variant: "card", tagLimit: 3 }),
  );
  return card;
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

async function refreshBoard() {
  if (!els.refreshPosts) return;
  let refreshed = false;
  els.refreshPosts.disabled = true;
  els.refreshPosts.classList.add("is-loading");
  els.refreshPosts.setAttribute("aria-busy", "true");
  try {
    await loadPosts({ seedWhenEmpty: false });
    refreshed = true;
    setMessage("");
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    els.refreshPosts.disabled = false;
    els.refreshPosts.classList.remove("is-loading");
    els.refreshPosts.removeAttribute("aria-busy");
    if (refreshed) {
      els.refreshPosts.classList.add("is-confirmed");
      window.setTimeout(() => els.refreshPosts?.classList.remove("is-confirmed"), 320);
    }
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

els.navFilters.forEach((button) => {
  button.addEventListener("click", () => setFilter(button.dataset.filter || "all"));
});
els.searchInput.addEventListener("input", () => {
  state.query = els.searchInput.value;
  renderPostList();
});
els.refreshPosts.addEventListener("click", refreshBoard);
els.focusComposer.addEventListener("click", () => {
  els.composerCard.scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => els.postForm.elements.title.focus(), 280);
});
els.postForm.addEventListener("submit", createPost);

loadPosts().catch((error) => setMessage(error.message, true));
