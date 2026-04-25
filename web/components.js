export const categoryLabels = {
  announcements: "ANNOUNCE",
  syntax: "LANGUAGE",
  ide: "TOOLCHAIN",
  showcase: "SHOWCASE",
  help: "HELP",
  general: "GENERAL",
};

export const categoryClass = {
  announcements: "is-yellow",
  syntax: "is-red",
  ide: "is-blue",
  showcase: "is-green",
  help: "is-purple",
  general: "is-ink",
};

export const categoryIcons = {
  announcements: "icon-spark",
  syntax: "icon-code",
  ide: "icon-monitor",
  showcase: "icon-spark",
  help: "icon-help",
  general: "icon-grid",
};

const categoryOptions = [
  ["syntax", "Language"],
  ["ide", "Toolchain"],
  ["showcase", "Showcase"],
  ["help", "Help"],
  ["general", "General"],
  ["announcements", "Announcements"],
];

const userColorPalette = [
  "#e63946",
  "#4ea8de",
  "#2ecc71",
  "#f1c40f",
  "#9b59b6",
  "#ff7a45",
  "#00b8a9",
  "#6c5ce7",
];

export function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.classList.add("icon");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `#${name}`);
  svg.append(use);
  return svg;
}

export function textSpan(text) {
  const span = document.createElement("span");
  span.textContent = text;
  return span;
}

export function iconField({
  className = "",
  iconName,
  name,
  control = "input",
  type,
  value,
  placeholder,
  rows,
  maxLength,
  required = false,
  autocomplete,
  form,
} = {}) {
  const label = document.createElement("label");
  label.className = ["icon-field", className].filter(Boolean).join(" ");

  const iconShell = document.createElement("span");
  iconShell.className = "icon-field-icon";
  iconShell.append(icon(iconName));

  const field = document.createElement(control);
  field.name = name;
  if (type) field.type = type;
  if (value !== undefined) field.value = value;
  if (placeholder) field.placeholder = placeholder;
  if (rows) field.rows = rows;
  if (maxLength) field.maxLength = maxLength;
  if (required) field.required = true;
  if (autocomplete) field.autocomplete = autocomplete;
  if (form) field.setAttribute("form", form);

  label.append(iconShell, field);
  return label;
}

export function iconTitle({
  className = "",
  href,
  text,
  iconName,
  markerClassName = "",
  markerLabel = "",
  markerTitle = markerLabel,
  as = "span",
} = {}) {
  const title = document.createElement(href ? "a" : as);
  title.className = ["icon-title", className].filter(Boolean).join(" ");
  if (href) title.href = href;

  const marker = document.createElement("span");
  marker.className = ["title-marker", markerClassName].filter(Boolean).join(" ");
  if (markerLabel) marker.setAttribute("aria-label", markerLabel);
  if (markerTitle) marker.title = markerTitle;
  marker.append(icon(iconName));

  const label = document.createElement("span");
  label.className = "icon-title-text";
  label.textContent = text || "";

  title.append(marker, label);
  return title;
}

export function userField(options = {}) {
  return iconField({
    className: ["author-field", options.className].filter(Boolean).join(" "),
    iconName: "icon-user",
    name: "author",
    value: options.value ?? "Styio User",
    maxLength: options.maxLength ?? 48,
    required: options.required ?? true,
    autocomplete: options.autocomplete,
    form: options.form,
  });
}

export function textAreaField(options = {}) {
  return iconField({
    className: options.className,
    iconName: options.iconName ?? "icon-lines",
    name: options.name,
    control: "textarea",
    placeholder: options.placeholder,
    rows: options.rows,
    maxLength: options.maxLength,
    required: options.required,
    form: options.form,
  });
}

export function categorySelectField({ className = "category-field", name = "category", value = "syntax" } = {}) {
  const label = document.createElement("label");
  label.className = ["icon-field", className].filter(Boolean).join(" ");

  const iconShell = document.createElement("span");
  iconShell.className = "icon-field-icon";
  iconShell.append(icon("icon-grid"));

  const select = document.createElement("select");
  select.name = name;
  select.required = true;
  for (const [optionValue, labelText] of categoryOptions) {
    const option = document.createElement("option");
    option.value = optionValue;
    option.textContent = labelText;
    option.selected = optionValue === value;
    select.append(option);
  }

  label.append(iconShell, select);
  return label;
}

export function tagsField(options = {}) {
  return iconField({
    className: options.className ?? "tag-field",
    iconName: "icon-tag",
    name: "tags",
    maxLength: options.maxLength ?? 120,
    placeholder: options.placeholder,
  });
}

export function bindUserFieldColor(field, getName) {
  const iconShell = field?.querySelector("span");
  const input = field?.querySelector("input");
  const readName = getName || (() => input?.value || "Styio User");
  const update = () => {
    if (iconShell) applyUserColor(iconShell, readName());
  };
  input?.addEventListener("input", update);
  update();
  return update;
}

export function categoryPill(category, options = {}) {
  const label = categoryLabels[category] || category;
  const tagName = options.href ? "a" : options.onClick ? "button" : options.as || "span";
  const pill = document.createElement(tagName);
  pill.className = [
    "category-pill",
    categoryClass[category] || "is-ink",
    options.className,
    options.onClick || options.href ? "is-interactive" : "",
  ]
    .filter(Boolean)
    .join(" ");
  pill.title = label;
  pill.dataset.category = category;
  pill.setAttribute("aria-label", label);
  if (options.href) pill.href = options.href;
  if (tagName === "button") pill.type = "button";
  if (options.onClick) pill.addEventListener("click", (event) => options.onClick(event, category));
  pill.append(icon(categoryIcons[category] || "icon-grid"), textSpan(label));
  return pill;
}

export function authorTimestamp({ author, timestamp, format = relativeTime }) {
  return iconMeta("icon-user", `${author} / ${format(timestamp)}`);
}

export function postTopline(post, { variant = "card", timeFormatter = relativeTime, category = {} } = {}) {
  const line = document.createElement("div");
  line.className = variant === "detail" ? "detail-header" : "post-topline";
  line.append(
    categoryPill(post.category, category),
    authorTimestamp({ author: post.author, timestamp: post.updated_at || post.created_at, format: timeFormatter }),
  );
  return line;
}

export function postFooter(post, { variant = "card", tagLimit = 3, liked = false, onReact } = {}) {
  const footer = document.createElement("div");
  footer.className = ["post-footer", variant === "detail" ? "detail-footer" : "card-footer"].join(" ");
  footer.append(
    tagRow(post.tags || [], { limit: tagLimit }),
    postStats(post, { variant, liked, onReact }),
  );
  return footer;
}

export function tagRow(tags, { limit = Infinity } = {}) {
  const row = document.createElement("div");
  row.className = "tag-row";
  for (const tag of tags.slice(0, limit)) {
    const item = document.createElement("span");
    item.append(icon("icon-tag"), document.createTextNode(tag));
    row.append(item);
  }
  return row;
}

export function postStats(post, { variant = "card", liked = false, onReact } = {}) {
  const stats = document.createElement("div");
  stats.className = ["post-stats", variant === "detail" ? "detail-stats" : ""].filter(Boolean).join(" ");
  stats.append(
    reactionChip(post, { variant, liked, onReact }),
    statChip({ iconName: "icon-message", value: post.comments?.length || 0, label: "Replies" }),
    statChip({ iconName: "icon-eye", value: post.views || 1, label: "Views" }),
  );
  return stats;
}

export function reactionChip(post, { variant = "card", liked = false, onReact } = {}) {
  if (variant === "detail" && onReact) {
    return statChip({
      iconName: "icon-signal",
      value: post.reactions || 0,
      label: "Likes",
      as: "button",
      className: `stat-button like-button${liked ? " is-liked" : ""}`,
      pressed: liked,
      onClick: onReact,
    });
  }
  return statChip({ iconName: "icon-signal", value: post.reactions || 0, label: "Likes" });
}

export function statChip({ iconName, value, label, as = "span", className = "", pressed, onClick } = {}) {
  const chip = document.createElement(as);
  chip.className = ["stat-chip", className].filter(Boolean).join(" ");
  chip.title = label;
  chip.setAttribute("aria-label", `${label}: ${value}`);
  if (as === "button") {
    chip.type = "button";
    chip.setAttribute("aria-pressed", pressed ? "true" : "false");
  }
  if (onClick) chip.addEventListener("click", onClick);
  chip.append(icon(iconName));
  const number = document.createElement("strong");
  number.textContent = String(value);
  chip.append(number);
  return chip;
}

export function iconMeta(iconName, text) {
  const meta = document.createElement("span");
  meta.className = "icon-meta";
  meta.append(icon(iconName), document.createTextNode(text));
  return meta;
}

export function postPreview(post) {
  const preview = document.createElement("div");
  preview.className = "post-preview";

  const excerpt = document.createElement("p");
  excerpt.className = "post-excerpt";
  excerpt.textContent = excerptFromBody(post.body);
  preview.append(excerpt);

  const thumbnailUrl = extractImageUrl(post.body);
  if (thumbnailUrl) {
    const thumbnail = document.createElement("img");
    thumbnail.className = "post-thumbnail";
    thumbnail.src = thumbnailUrl;
    thumbnail.alt = "";
    thumbnail.loading = "lazy";
    thumbnail.decoding = "async";
    preview.append(thumbnail);
  }
  return preview;
}

export function emptyState(iconName, text) {
  const wrapper = document.createElement("div");
  wrapper.className = "empty-state";
  wrapper.append(icon(iconName), textSpan(text));
  return wrapper;
}

export function readPostForm(form) {
  const data = new FormData(form);
  return {
    author: String(data.get("author") || ""),
    title: String(data.get("title") || ""),
    category: String(data.get("category") || "general"),
    tags: splitTags(String(data.get("tags") || "")),
    body: String(data.get("body") || ""),
  };
}

export function splitTags(value) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 5);
}

export function initials(name) {
  const clean = String(name || "U").trim();
  return clean.slice(0, 1).toUpperCase();
}

export function colorForAuthor(name) {
  const normalized = String(name || "user").trim().toLowerCase();
  let hash = 0;
  for (const char of normalized) {
    hash = (hash * 31 + char.codePointAt(0)) >>> 0;
  }
  return userColorPalette[hash % userColorPalette.length];
}

export function applyUserColor(element, name) {
  element.style.setProperty("--user-color", colorForAuthor(name));
}

export function sameAuthor(a, b) {
  return String(a || "").trim().toLowerCase() === String(b || "").trim().toLowerCase();
}

export function relativeTime(value) {
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

export function formatShortDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "";
  const pad = (part) => String(part).padStart(2, "0");
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function excerptFromBody(body) {
  const text = stripImageSyntax(String(body || ""))
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!text) return "";
  const sentences = text.match(/[^。！？!?]+[。！？!?]?/g) || [text];
  const excerpt = sentences.slice(0, 2).join("").trim();
  return excerpt.length > 180 ? `${excerpt.slice(0, 180).trim()}...` : excerpt;
}

export function extractImageUrl(body) {
  const text = String(body || "");
  const markdown = text.match(/!\[[^\]]*]\((https?:\/\/[^)\s]+)\)/i);
  if (markdown) return cleanImageUrl(markdown[1]);
  const html = text.match(/<img[^>]+src=["'](https?:\/\/[^"']+)["'][^>]*>/i);
  if (html) return cleanImageUrl(html[1]);
  const raw = text.match(/https?:\/\/[^\s)]+?\.(?:png|jpe?g|gif|webp|avif)(?:\?[^\s)]*)?/i);
  return raw ? cleanImageUrl(raw[0]) : "";
}

function cleanImageUrl(url) {
  return String(url).replace(/[.,;!?，。；！？]+$/, "");
}

function stripImageSyntax(body) {
  return body
    .replace(/!\[[^\]]*]\([^)]+\)/g, " ")
    .replace(/<img[^>]*>/gi, " ");
}
