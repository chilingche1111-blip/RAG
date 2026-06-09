const topicList = document.getElementById("topic-list");
const topicSelect = document.getElementById("topic");
const suggestionList = document.getElementById("suggestion-list");
const topicCount = document.getElementById("topic-count");
const queryForm = document.getElementById("query-form");
const refreshSuggestionsButton = document.getElementById("refresh-suggestions");
const questionInput = document.getElementById("question");
const statusLabel = document.getElementById("status-label");
const emptyState = document.getElementById("empty-state");
const result = document.getElementById("result");
const resultTopic = document.getElementById("result-topic");
const resultQuestion = document.getElementById("result-question");
const confidenceBadge = document.getElementById("confidence-badge");
const answerText = document.getElementById("answer-text");
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

function renderResult(payload) {
  emptyState.classList.add("hidden");
  result.classList.remove("hidden");

  resultTopic.textContent = `主题：${payload.topic} · 生成：${payload.answer_backend}`;
  resultQuestion.textContent = payload.question;
  confidenceBadge.textContent = `置信度：${payload.confidence_label}`;
  answerText.textContent = payload.answer;
  documentationHint.textContent = payload.documentation_hint;

  relatedQuestionList.innerHTML = "";
  payload.related_questions.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    relatedQuestionList.appendChild(li);
  });

  citationList.innerHTML = "";
  payload.retrieved_chunks.forEach((chunk) => {
    const link = chunk.source_url
      ? `<a class="citation-link" href="${chunk.source_url}" target="_blank" rel="noreferrer">原始文档</a>`
      : "";
    const card = document.createElement("article");
    card.className = "citation-card";
    card.innerHTML = `
      <h5>${chunk.source_name}</h5>
      <p>${chunk.text}</p>
      <div class="citation-meta">
        <span>${chunk.topic} · score ${chunk.score}</span>
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
loadSuggestions();
