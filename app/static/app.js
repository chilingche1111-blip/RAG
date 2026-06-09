const topicList = document.getElementById("topic-list");
const topicSelect = document.getElementById("topic");
const suggestionList = document.getElementById("suggestion-list");
const topicCount = document.getElementById("topic-count");
const queryForm = document.getElementById("query-form");
const refreshSuggestionsButton = document.getElementById("refresh-suggestions");
const questionInput = document.getElementById("question");
const llmProviderSelect = document.getElementById("llm-provider");
const llmModelInput = document.getElementById("llm-model");
const providerCount = document.getElementById("provider-count");
const providerList = document.getElementById("provider-list");
const statusLabel = document.getElementById("status-label");
const emptyState = document.getElementById("empty-state");
const result = document.getElementById("result");
const resultTopic = document.getElementById("result-topic");
const resultQuestion = document.getElementById("result-question");
const confidenceBadge = document.getElementById("confidence-badge");
const backendBadge = document.getElementById("backend-badge");
const chunkUsage = document.getElementById("chunk-usage");
const summaryText = document.getElementById("summary-text");
const keyPointList = document.getElementById("key-point-list");
const caveatList = document.getElementById("caveat-list");
const documentationHint = document.getElementById("documentation-hint");
const relatedQuestionList = document.getElementById("related-question-list");
const citationList = document.getElementById("citation-list");

async function fetchTopics() {
  const response = await fetch("/api/v1/topics");
  const topics = await response.json();

  topicCount.textContent = `${topics.length} 个主题`;
  topicList.innerHTML = "";

  topics.forEach((topic) => {
    const card = document.createElement("article");
    card.className = "topic-card";
    const sources = topic.official_sources
      .map(
        (source) =>
          `<a class="source-pill" href="${source.url}" target="_blank" rel="noreferrer">${source.name}</a>`,
      )
      .join("");
    card.innerHTML = `
      <h3>${topic.label}</h3>
      <p>${topic.description}</p>
      <div class="source-list">${sources}</div>
    `;
    card.addEventListener("click", () => {
      topicSelect.value = topic.id;
      loadSuggestions(topic.id);
      questionInput.focus();
    });
    topicList.appendChild(card);

    const option = document.createElement("option");
    option.value = topic.id;
    option.textContent = topic.label;
    topicSelect.appendChild(option);
  });
}

async function fetchLLMOptions() {
  const response = await fetch("/api/v1/llm/options");
  const providers = await response.json();

  providerCount.textContent = `${providers.length} 个`;
  providerList.innerHTML = "";

  providers.forEach((provider) => {
    const option = document.createElement("option");
    option.value = provider.provider_id;
    option.textContent = `${provider.label} · ${provider.default_model}`;
    llmProviderSelect.appendChild(option);

    const card = document.createElement("article");
    card.className = "provider-card";
    const baseUrlLabel = provider.base_url ? provider.base_url : "native endpoint";
    card.innerHTML = `
      <div class="provider-card-top">
        <strong>${provider.label}</strong>
        <span class="provider-type">${provider.provider_type}</span>
      </div>
      <p>${provider.description}</p>
      <div class="provider-meta">
        <span>${provider.default_model}</span>
        <span>${provider.api_key_env}</span>
      </div>
      <div class="provider-meta provider-meta-soft">
        <span>${baseUrlLabel}</span>
      </div>
    `;
    card.addEventListener("click", () => {
      llmProviderSelect.value = provider.provider_id;
      llmModelInput.value = provider.default_model;
    });
    providerList.appendChild(card);
  });
}

async function loadSuggestions(topic = "") {
  const params = new URLSearchParams();
  if (topic) {
    params.set("topic", topic);
  }

  const response = await fetch(`/api/v1/suggestions?${params.toString()}`);
  const data = await response.json();

  suggestionList.innerHTML = "";
  data.questions.forEach((question) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = question;
    chip.addEventListener("click", () => {
      questionInput.value = question;
      questionInput.focus();
    });
    suggestionList.appendChild(chip);
  });
}

function renderList(target, items) {
  target.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    target.appendChild(li);
  });
}

function renderResult(payload) {
  emptyState.classList.add("hidden");
  result.classList.remove("hidden");

  resultTopic.textContent = `主题：${payload.topic}`;
  resultQuestion.textContent = payload.question;
  confidenceBadge.textContent = `置信度：${payload.confidence_label}`;
  backendBadge.textContent = `生成后端：${payload.answer_backend}`;
  chunkUsage.textContent = `引用 Chunk：${payload.used_chunk_ids.join(", ") || "无"}`;
  summaryText.textContent = payload.summary;
  documentationHint.textContent = payload.documentation_hint;

  renderList(keyPointList, payload.key_points);
  renderList(caveatList, payload.caveats);
  renderList(relatedQuestionList, payload.related_questions);

  citationList.innerHTML = "";
  payload.retrieved_chunks.forEach((chunk) => {
    const link = chunk.source_url
      ? `<a class="citation-link" href="${chunk.source_url}" target="_blank" rel="noreferrer">原始文档</a>`
      : "";
    const rerank = chunk.rerank_score !== null ? ` · rerank ${chunk.rerank_score}` : "";
    const card = document.createElement("article");
    card.className = "citation-card";
    card.innerHTML = `
      <h5>${chunk.source_name}</h5>
      <p>${chunk.text}</p>
      <div class="citation-meta">
        <span>${chunk.topic} · score ${chunk.score}${rerank}</span>
        <span>${link}</span>
      </div>
    `;
    citationList.appendChild(card);
  });
}

async function runQuery(event) {
  event.preventDefault();
  statusLabel.textContent = "生成中";

  const payload = {
    question: questionInput.value.trim(),
    top_k: 4,
  };

  if (topicSelect.value) {
    payload.topic = topicSelect.value;
  }
  if (llmProviderSelect.value) {
    payload.llm_provider = llmProviderSelect.value;
  }
  if (llmModelInput.value.trim()) {
    payload.llm_model = llmModelInput.value.trim();
  }

  const response = await fetch("/api/v1/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  renderResult(data);
  statusLabel.textContent = "已完成";
}

topicSelect.addEventListener("change", () => loadSuggestions(topicSelect.value));
refreshSuggestionsButton.addEventListener("click", () => loadSuggestions(topicSelect.value));
queryForm.addEventListener("submit", runQuery);

fetchTopics();
fetchLLMOptions();
loadSuggestions();
