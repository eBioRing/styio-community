import {
  applyUserColor,
  bindUserFieldColor,
  categoryClass,
  emptyState,
  formatShortDate,
  initials,
  postFooter,
  postTopline,
  relativeTime,
  sameAuthor,
  textAreaField,
  userField,
} from "./components.js";

const state = {
  post: null,
  postId: postIdFromLocation(),
  hasReacted: false,
  currentAuthor: "Styio User",
};

const els = {
  postDetail: document.querySelector("#postDetail"),
  replyList: document.querySelector("#replyList"),
  replyForm: document.querySelector("#replyForm"),
  replyAuthorSlot: document.querySelector("#replyAuthorSlot"),
  replyBodySlot: document.querySelector("#replyBodySlot"),
  message: document.querySelector("#message"),
};

let updateReplyAuthorColor = () => {};
mountReplyComposerFields();

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

async function loadPost() {
  if (!state.postId) {
    throw new Error("missing post id");
  }
  const payload = await api(`/api/forum/posts/${encodeURIComponent(state.postId)}`);
  state.post = payload.post;
  render();
}

function mountReplyComposerFields() {
  const authorField = userField({ value: state.currentAuthor });
  els.replyAuthorSlot?.replaceChildren(authorField);
  updateReplyAuthorColor = bindUserFieldColor(authorField, currentAuthor);

  els.replyBodySlot?.replaceChildren(
    textAreaField({
      className: "composer-body",
      name: "body",
      rows: 4,
      maxLength: 2000,
      required: true,
      placeholder: "加入你的观点、复现步骤或补充资料。",
    }),
  );
}

function render() {
  if (!state.post) return;
  document.title = `${state.post.title} / Styio Community`;
  renderPostDetail();
  renderReplies();
  updateReplyAuthorColor();
}

function renderPostDetail() {
  const post = state.post;
  els.postDetail.className = ["detail-card", categoryClass[post.category] || "is-ink"].join(" ");
  const wrapper = document.createElement("div");
  wrapper.className = "thread-detail";

  const title = document.createElement("h1");
  title.textContent = post.title;

  const body = document.createElement("p");
  body.className = "thread-body";
  body.textContent = post.body;

  wrapper.append(
    postTopline(post, { variant: "detail", timeFormatter: formatShortDate }),
    title,
    body,
    postFooter(post, {
      variant: "detail",
      tagLimit: Infinity,
      liked: state.hasReacted,
      onReact: reactToPost,
    }),
  );
  els.postDetail.replaceChildren(wrapper);
}

function renderReplies() {
  const replies = state.post?.comments || [];
  if (replies.length === 0) {
    const empty = document.createElement("li");
    empty.className = "reply-empty";
    empty.append(emptyState("icon-message", "0"));
    els.replyList.replaceChildren(empty);
    return;
  }
  els.replyList.replaceChildren(...replies.map(renderReply));
}

function renderReply(comment) {
  const item = document.createElement("li");
  const isOwn = sameAuthor(comment.author, currentAuthor());
  item.className = `reply-item ${isOwn ? "is-own" : "is-other"}`;

  const avatar = document.createElement("span");
  avatar.className = "reply-avatar";
  avatar.textContent = initials(comment.author);
  applyUserColor(avatar, comment.author);

  const bubble = document.createElement("div");
  bubble.className = "reply-bubble";

  const meta = document.createElement("div");
  meta.className = "reply-meta";
  const author = document.createElement("strong");
  author.textContent = comment.author;
  const time = document.createElement("span");
  time.textContent = relativeTime(comment.created_at);
  meta.append(author, time);

  const body = document.createElement("p");
  body.textContent = comment.body;
  bubble.append(meta, body);
  item.append(avatar, bubble);
  return item;
}

async function createReply(event) {
  event.preventDefault();
  const data = new FormData(els.replyForm);
  const author = String(data.get("author") || "");
  try {
    const payload = await api(`/api/forum/posts/${encodeURIComponent(state.postId)}/comments`, {
      method: "POST",
      body: JSON.stringify({
        author,
        body: String(data.get("body") || ""),
      }),
    });
    els.replyForm.elements.body.value = "";
    state.currentAuthor = author.trim() || state.currentAuthor;
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
    state.hasReacted = true;
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

function currentAuthor() {
  return String(els.replyForm?.elements.author?.value || state.currentAuthor || "Styio User").trim();
}

els.replyForm.elements.author.addEventListener("input", () => {
  state.currentAuthor = currentAuthor();
  updateReplyAuthorColor();
  renderReplies();
});
els.replyForm.addEventListener("submit", createReply);
loadPost().catch((error) => {
  els.postDetail.replaceChildren();
  els.replyForm.hidden = true;
  setMessage(error.message, true);
});
