"use strict";

const state = { stories: [] };
const $ = (selector) => document.querySelector(selector);
const dateText = (value, withTime = false) => {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "Date unavailable";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    ...(withTime ? { timeStyle: "short" } : {}),
  }).format(date);
};

function addEvidence(container, story) {
  const items = [
    ...story.cves,
    ...(story.cvss_score ? [`CVSS ${story.cvss_score}`] : []),
    ...(story.active_exploitation ? ["ACTIVE EXPLOITATION"] : []),
    ...(story.known_exploited ? ["CISA KEV"] : []),
    ...(story.patch_available ? ["PATCH AVAILABLE"] : []),
    ...story.affected_vendors,
    ...story.affected_products,
    ...story.mitre_techniques,
  ];
  items.forEach((item) => {
    const chip = document.createElement("span");
    chip.textContent = item;
    container.append(chip);
  });
}

function storyCard(story) {
  const card = $("#story-template").content.firstElementChild.cloneNode(true);
  const severity = card.querySelector(".severity");
  severity.textContent = story.severity;
  severity.classList.add(story.severity);
  card.querySelector(".score").textContent = `SCORE ${story.importance_score}/100`;
  card.querySelector(".category").textContent = story.category;
  card.querySelector("h3").textContent = story.title;
  card.querySelector(".summary").textContent = story.summary;
  card.querySelector(".why p").textContent = story.why_it_matters;
  addEvidence(card.querySelector(".evidence"), story);
  card.querySelector(".source").textContent = story.source;
  card.querySelector("time").textContent = dateText(story.published_at);
  const link = card.querySelector("a");
  link.href = story.source_url;
  link.setAttribute("aria-label", `Read ${story.title} at ${story.source}`);
  return card;
}

function render() {
  const category = $("#category-filter").value;
  const severity = $("#severity-filter").value;
  const stories = state.stories.filter((story) =>
    (!category || story.category === category) && (!severity || story.severity === severity));
  const grid = $("#story-grid");
  grid.replaceChildren(...stories.map(storyCard));
  $("#result-count").textContent = `${stories.length} ${stories.length === 1 ? "story" : "stories"}`;
  $("#empty-state").hidden = stories.length !== 0;
}

function renderLead(story) {
  if (!story) return;
  const section = $("#top-story");
  const card = document.createElement("article");
  card.className = "lead-card";
  card.dataset.score = story.importance_score;
  const meta = document.createElement("p");
  meta.className = "category";
  meta.textContent = `${story.severity} · ${story.category} · ${story.source}`;
  const title = document.createElement("h2");
  title.textContent = story.title;
  const summary = document.createElement("p");
  summary.textContent = story.summary;
  const link = document.createElement("a");
  link.href = story.source_url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Open original reporting ↗";
  card.append(meta, title, summary, link);
  $("#top-story-content").replaceChildren(card);
  section.hidden = false;
}

async function init() {
  try {
    const response = await fetch("data/ai_cyber_digest.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const digest = await response.json();
    if (!Array.isArray(digest.stories)) throw new Error("Invalid digest");
    state.stories = digest.stories;
    $("#generated-at").textContent = dateText(digest.generated_at, true);
    $("#metric-collected").textContent = digest.articles_collected;
    $("#metric-published").textContent = digest.stories_published ?? digest.stories.length;
    $("#metric-critical").textContent = digest.critical_count;
    $("#metric-high").textContent = digest.high_count;
    $("#metric-other").textContent = digest.medium_count + digest.low_count;
    [...new Set(state.stories.map((story) => story.category))].sort().forEach((category) => {
      const option = document.createElement("option");
      option.value = option.textContent = category;
      $("#category-filter").append(option);
    });
    renderLead(state.stories[0]);
    render();
  } catch (error) {
    $("#generated-at").textContent = "Digest unavailable";
    $("#empty-state").textContent = "The validated intelligence feed could not be loaded. Please try again later.";
    $("#empty-state").hidden = false;
    console.error(error);
  }
}

$("#category-filter").addEventListener("change", render);
$("#severity-filter").addEventListener("change", render);
init();
