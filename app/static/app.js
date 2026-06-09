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
const llmStatusSummary = document.getElementById("llm-status-summary");
const defaultProviderBadge = document.getElementById("default-provider-badge");
const crawlSourceSelect = document.getElementById("crawl-source");
const crawlLimitInput = document.getElementById("crawl-limit");
const rebuildTopicSelect = document.getElementById("rebuild-topic");
const crawlButton = document.getElementById("crawl-button");
const rebuildButton = document.getElementById("rebuild-button");
const evalButton = document.getElementById("eval-button");
const opsStatus = document.getElementById("ops-status");
const indexStatList = document.getElementById("index-stat-list");
const opsRefreshLabel = document.getElementById("ops-refresh-label");
const evalRunLabel = document.getElementById("eval-run-label");
const evalSummaryList = document.getElementById("eval-summary-list");
const evalFailureList = document.getElementById("eval-failure-list");
const sourceStatusList = document.getElementById("source-status-list");
const sourceCountLabel = document.getElementById("source-count-label");
const recentLogList = document.getElementById("recent-log-list");
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
let providerRegistry = [];

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function highlightCitationCard(chunkId) {
  const card = document.getElementById(`citation-${chunkId}`);
  if (!card) {
    return;
  }
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  card.classList.add("citation-card-active");
  window.setTimeout(() => card.classList.remove("citation-card-active"), 1800);
}

function renderRichText(text) {
  const escaped = escapeHtml(text);
  const withCode = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");
  const withCitations = withCode.replace(/\[([a-z0-9-]+)\]/gi, (_match, chunkId) => {
    return `<button type="button" class="inline-citation" data-chunk-id="${chunkId}">[${chunkId}]</button>`;
  });
  return withCitations.replace(/\n/g, "<br />");
}

function bindCitationButtons(target) {
  target.querySelectorAll(".inline-citation").forEach((button) => {
    button.addEventListener("click", () => {
      highlightCitationCard(button.dataset.chunkId);
    });
  });
}

async function parseResponse(response) {
  const payload = await response.json();
  if (!response.ok) {
    const detail = payload.detail || payload.message || "Request failed.";
    throw new Error(detail);
  }
  return payload;
}

function setOpsStatus(message, tone = "soft") {
  opsStatus.textContent = message;
  opsStatus.dataset.tone = tone;
}

function formatTimestamp(value) {
  if (!value) {
    return "未记录";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

function renderMetricCards(target, items) {
  target.innerHTML = "";
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "metric-card";
    card.innerHTML = `
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <p>${escapeHtml(item.note || "")}</p>
    `;
    target.appendChild(card);
  });
}

async function fetchTopics() {
  const response = await fetch("/api/v1/topics");
  const topics = await parseResponse(response);

  topicCount.textContent = `${topics.length} 个主题`;
  topicList.innerHTML = "";
  topicSelect.innerHTML = '<option value="">全部</option>';
  rebuildTopicSelect.innerHTML = '<option value="">全部 Topic</option>';

  topics.forEach((topic) => {
    const card = document.createElement("article");
    card.className = "topic-card";
    const sources = topic.official_sources
      .map(
        (source) =>
          `<a class="source-pill" href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.name)}</a>`,
      )
      .join("");
    card.innerHTML = `
      <h3>${escapeHtml(topic.label)}</h3>
      <p>${escapeHtml(topic.description)}</p>
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

    const rebuildOption = document.createElement("option");
    rebuildOption.value = topic.id;
    rebuildOption.textContent = topic.label;
    rebuildTopicSelect.appendChild(rebuildOption);
  });
}

function syncProviderSelectionUI() {
  providerList.querySelectorAll(".provider-card").forEach((card) => {
    const active = card.dataset.providerId === llmProviderSelect.value;
    card.classList.toggle("provider-card-active", active);
  });
}

function applyProviderDefaults(providerId) {
  const provider = providerRegistry.find((item) => item.provider_id === providerId);
  if (!provider) {
    return;
  }
  llmModelInput.value = provider.default_model;
}

async function fetchLLMOptions() {
  const [optionsResponse, healthResponse] = await Promise.all([
    fetch("/api/v1/llm/options"),
    fetch("/api/v1/llm/health"),
  ]);
  const providers = await parseResponse(optionsResponse);
  const health = await parseResponse(healthResponse);
  const healthById = new Map(health.map((item) => [item.provider_id, item]));
  const configuredCount = health.filter((item) => item.configured).length;
  const defaultProvider = health.find((item) => item.selected_by_default);
  providerRegistry = providers;

  providerCount.textContent = `${providers.length} 个 · ${configuredCount} 已配置`;
  llmStatusSummary.textContent = configuredCount
    ? `${configuredCount}/${health.length} 个 provider key 已配置`
    : "未检测到 provider key，将回退到 grounded answer";
  defaultProviderBadge.textContent = defaultProvider
    ? `默认：${defaultProvider.label}`
    : "默认 provider 未设置";
  providerList.innerHTML = "";
  llmProviderSelect.innerHTML = '<option value="">默认</option>';

  providers.forEach((provider) => {
    const providerHealth = healthById.get(provider.provider_id);
    const option = document.createElement("option");
    option.value = provider.provider_id;
    option.textContent = `${provider.label} · ${provider.default_model}`;
    llmProviderSelect.appendChild(option);

    const card = document.createElement("article");
    card.className = "provider-card";
    card.dataset.providerId = provider.provider_id;
    const baseUrlLabel = provider.base_url ? provider.base_url : "native endpoint";
    const stateLabel = providerHealth?.configured ? "已配置" : "缺少 Key";
    const stateClass = providerHealth?.configured
      ? "provider-state-ready"
      : "provider-state-missing";
    const defaultLabel = providerHealth?.selected_by_default
      ? '<span class="provider-flag">默认</span>'
      : "";
    card.innerHTML = `
      <div class="provider-card-top">
        <strong>${escapeHtml(provider.label)}</strong>
        <div class="provider-card-badges">
          ${defaultLabel}
          <span class="provider-state ${stateClass}">${stateLabel}</span>
        </div>
      </div>
      <p>${escapeHtml(provider.description)}</p>
      <div class="provider-meta">
        <span>${escapeHtml(provider.default_model)}</span>
        <span>${escapeHtml(provider.api_key_env)}</span>
      </div>
      <div class="provider-meta provider-meta-soft">
        <span>${escapeHtml(provider.provider_type)}</span>
        <span>${escapeHtml(baseUrlLabel)}</span>
      </div>
      <div class="provider-note">${escapeHtml(providerHealth?.message || "未获取到状态信息。")}</div>
    `;
    card.addEventListener("click", () => {
      llmProviderSelect.value = provider.provider_id;
      applyProviderDefaults(provider.provider_id);
      syncProviderSelectionUI();
    });
    providerList.appendChild(card);
  });

  syncProviderSelectionUI();
}

async function fetchIndexStats() {
  const response = await fetch("/api/v1/index/stats");
  const stats = await parseResponse(response);
  opsRefreshLabel.textContent = `更新于 ${formatTimestamp(stats.last_rebuild_at)}`;
  renderMetricCards(indexStatList, [
    {
      label: "知识文档",
      value: `${stats.document_count}`,
      note: `覆盖 ${stats.topic_count} 个 topic`,
    },
    {
      label: "Chunk 数",
      value: `${stats.chunk_count}`,
      note: stats.retrieval_backend,
    },
    {
      label: "Rerank",
      value: stats.reranker_backend,
      note: `生成层 ${stats.generation_backend}`,
    },
    {
      label: "查询日志",
      value: `${stats.query_log_size}`,
      note: "最近请求滚动窗口",
    },
  ]);
}

async function fetchDocSources() {
  const response = await fetch("/api/v1/docs/sources");
  const sources = await parseResponse(response);
  sourceCountLabel.textContent = `${sources.length} 个来源`;
  crawlSourceSelect.innerHTML = '<option value="all">全部来源</option>';
  sourceStatusList.innerHTML = "";

  sources.forEach((source) => {
    const option = document.createElement("option");
    option.value = source.source_id;
    option.textContent = `${source.label} · ${source.topic}`;
    crawlSourceSelect.appendChild(option);

    const card = document.createElement("article");
    card.className = "source-status-card";
    card.innerHTML = `
      <div class="source-status-top">
        <strong>${escapeHtml(source.label)}</strong>
        <span class="provider-flag">${escapeHtml(source.topic)}</span>
      </div>
      <p>${escapeHtml(source.description)}</p>
      <div class="provider-meta">
        <span>max_pages ${source.max_pages}</span>
        <span>${source.allow_domains.join(", ")}</span>
      </div>
      <div class="provider-meta provider-meta-soft">
        <span>indexed ${source.indexed_document_count}</span>
        <span>crawled ${source.crawled_document_count}</span>
      </div>
      <div class="provider-note">last crawl: ${escapeHtml(formatTimestamp(source.last_crawled_at))}</div>
    `;
    sourceStatusList.appendChild(card);
  });
}

async function fetchRecentLogs() {
  const response = await fetch("/api/v1/admin/logs?limit=12");
  const logs = await parseResponse(response);
  recentLogList.innerHTML = "";
  if (!logs.length) {
    recentLogList.innerHTML = '<p class="empty-inline">暂无查询日志。</p>';
    return;
  }
  logs.forEach((log) => {
    const row = document.createElement("article");
    row.className = "compact-item";
    row.innerHTML = `
      <div class="compact-item-top">
        <strong>${escapeHtml(log.question)}</strong>
        <span>${escapeHtml(formatTimestamp(log.timestamp))}</span>
      </div>
      <p>${escapeHtml(log.topic)} · ${escapeHtml(log.answer_backend)} · ${escapeHtml(log.confidence_label)}</p>
      <div class="provider-note">top chunks: ${escapeHtml(log.top_chunk_ids || "无")}</div>
    `;
    recentLogList.appendChild(row);
  });
}

function renderEvalSummary(report) {
  evalRunLabel.textContent = `${report.passed_cases}/${report.total_cases} 通过`;
  renderMetricCards(evalSummaryList, [
    {
      label: "Pass Rate",
      value: `${Math.round(report.overall_pass_rate * 100)}%`,
      note: "整体通过率",
    },
    {
      label: "Retrieval Hit",
      value: `${Math.round(report.retrieval_hit_rate * 100)}%`,
      note: "命中预期 chunk",
    },
    {
      label: "Citation Hit",
      value: `${Math.round(report.citation_hit_rate * 100)}%`,
      note: "答案引用命中",
    },
    {
      label: "Term Coverage",
      value: `${Math.round(report.answer_term_coverage * 100)}%`,
      note: "关键术语覆盖率",
    },
  ]);
  evalFailureList.innerHTML = "";
  const failed = report.results.filter((item) => !item.passed).slice(0, 5);
  if (!failed.length) {
    evalFailureList.innerHTML = '<p class="empty-inline">当前运行未发现失败样例。</p>';
    return;
  }
  failed.forEach((item) => {
    const row = document.createElement("article");
    row.className = "compact-item";
    row.innerHTML = `
      <div class="compact-item-top">
        <strong>${escapeHtml(item.case_id)}</strong>
        <span>${escapeHtml(item.topic)}</span>
      </div>
      <p>${escapeHtml(item.question)}</p>
      <div class="provider-note">
        retrieval=${item.retrieval_hit} · citation=${item.citation_hit} · term=${item.answer_term_coverage}
      </div>
    `;
    evalFailureList.appendChild(row);
  });
}

async function runCrawl() {
  setOpsStatus("抓取中", "busy");
  const payload = {
    source_id: crawlSourceSelect.value || "all",
    incremental: true,
    rebuild_after: true,
  };
  const limit = Number.parseInt(crawlLimitInput.value, 10);
  if (!Number.isNaN(limit) && limit > 0) {
    payload.limit = limit;
  }
  try {
    const response = await fetch("/api/v1/docs/crawl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await parseResponse(response);
    const totalCreated = data.reports.reduce((sum, item) => sum + item.created_count, 0);
    const totalUpdated = data.reports.reduce((sum, item) => sum + item.updated_count, 0);
    setOpsStatus(
      `抓取完成：新增 ${totalCreated}，更新 ${totalUpdated}，重建 topic ${data.rebuilt_topics.join(", ") || "无"}`,
      "success",
    );
    await refreshOperatorData();
  } catch (error) {
    setOpsStatus(error.message || "抓取失败", "error");
  }
}

async function runRebuild() {
  setOpsStatus("重建中", "busy");
  const topics = rebuildTopicSelect.value ? [rebuildTopicSelect.value] : [];
  try {
    const response = await fetch("/api/v1/index/rebuild", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topics }),
    });
    const data = await parseResponse(response);
    setOpsStatus(
      `重建完成：${data.document_count} docs / ${data.chunk_count} chunks`,
      "success",
    );
    await refreshOperatorData();
  } catch (error) {
    setOpsStatus(error.message || "重建失败", "error");
  }
}

async function runEvaluation() {
  setOpsStatus("评测运行中", "busy");
  const payload = { top_k: 4 };
  if (rebuildTopicSelect.value) {
    payload.topic = rebuildTopicSelect.value;
  }
  try {
    const response = await fetch("/api/v1/evaluation/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await parseResponse(response);
    renderEvalSummary(data);
    setOpsStatus(
      `评测完成：通过 ${data.passed_cases}/${data.total_cases}`,
      "success",
    );
  } catch (error) {
    setOpsStatus(error.message || "评测失败", "error");
  }
}

async function refreshOperatorData() {
  await Promise.all([fetchIndexStats(), fetchDocSources(), fetchRecentLogs()]);
}

async function loadSuggestions(topic = "") {
  const params = new URLSearchParams();
  if (topic) {
    params.set("topic", topic);
  }

  const response = await fetch(`/api/v1/suggestions?${params.toString()}`);
  const data = await parseResponse(response);

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
    li.innerHTML = renderRichText(item);
    target.appendChild(li);
  });
  bindCitationButtons(target);
}

function renderResult(payload) {
  emptyState.classList.add("hidden");
  result.classList.remove("hidden");

  resultTopic.textContent = `主题：${payload.topic}`;
  resultQuestion.textContent = payload.question;
  confidenceBadge.textContent = `置信度：${payload.confidence_label}`;
  backendBadge.textContent = `生成后端：${payload.answer_backend}`;
  chunkUsage.textContent = `引用 Chunk：${payload.used_chunk_ids.join(", ") || "无"}`;
  summaryText.innerHTML = renderRichText(payload.summary);
  documentationHint.textContent = payload.documentation_hint;
  bindCitationButtons(summaryText);

  renderList(keyPointList, payload.key_points);
  renderList(caveatList, payload.caveats);
  renderList(relatedQuestionList, payload.related_questions);

  citationList.innerHTML = "";
  payload.retrieved_chunks.forEach((chunk) => {
    const link = chunk.source_url
      ? `<a class="citation-link" href="${escapeHtml(chunk.source_url)}" target="_blank" rel="noreferrer">原始文档</a>`
      : "";
    const rerank = chunk.rerank_score !== null ? ` · rerank ${chunk.rerank_score}` : "";
    const card = document.createElement("article");
    card.className = "citation-card";
    card.id = `citation-${chunk.chunk_id}`;
    card.innerHTML = `
      <h5>${escapeHtml(chunk.source_name)}</h5>
      <p>${escapeHtml(chunk.text)}</p>
      <div class="citation-meta">
        <span>${escapeHtml(chunk.topic)} · score ${chunk.score}${rerank}</span>
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

  try {
    const response = await fetch("/api/v1/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await parseResponse(response);
    renderResult(data);
    statusLabel.textContent = "已完成";
  } catch (error) {
    result.classList.add("hidden");
    emptyState.classList.remove("hidden");
    emptyState.textContent = error.message || "查询失败，请检查服务日志。";
    statusLabel.textContent = "失败";
  }
}

topicSelect.addEventListener("change", () => loadSuggestions(topicSelect.value));
refreshSuggestionsButton.addEventListener("click", () => loadSuggestions(topicSelect.value));
llmProviderSelect.addEventListener("change", () => {
  if (llmProviderSelect.value) {
    applyProviderDefaults(llmProviderSelect.value);
  }
  syncProviderSelectionUI();
});
queryForm.addEventListener("submit", runQuery);
crawlButton.addEventListener("click", runCrawl);
rebuildButton.addEventListener("click", runRebuild);
evalButton.addEventListener("click", runEvaluation);

fetchTopics();
fetchLLMOptions();
loadSuggestions();
refreshOperatorData();
