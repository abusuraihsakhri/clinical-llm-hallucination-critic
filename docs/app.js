const FLAGS = ["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"];
const form = document.querySelector("#critic-form");
const themeToggle = document.querySelector("#theme-toggle");
const resetButton = document.querySelector("#reset-button");
const statusChip = document.querySelector("#status-chip");
const alertCount = document.querySelector("#alert-count");
const integrityState = document.querySelector("#integrity-state");
const ruleList = document.querySelector("#rule-list");
const fingerprint = document.querySelector("#fingerprint");

function readInput() {
  return {
    taskId: document.querySelector("#task-id").value.trim(),
    targetId: document.querySelector("#target-id").value.trim(),
    primaryMetric: Number(document.querySelector("#primary-metric").value),
    secondaryMetric: Number(document.querySelector("#secondary-metric").value),
    statusDescriptor: document.querySelector("#status-descriptor").value.trim(),
    criticalFlag: document.querySelector("#critical-flag").checked,
  };
}

function evaluate(payload) {
  const rules = [];
  if (payload.primaryMetric > 25) {
    rules.push({ level: "elevated", title: "Primary threshold", detail: `${payload.primaryMetric} > 25` });
  }
  if (payload.criticalFlag || payload.secondaryMetric > 12) {
    rules.push({
      level: payload.criticalFlag ? "critical" : "elevated",
      title: payload.criticalFlag ? "Manual critical flag" : "Secondary threshold",
      detail: payload.criticalFlag ? "Critical flag enabled" : `${payload.secondaryMetric} > 12`,
    });
  }
  const matchedFlag = FLAGS.find((flag) => payload.statusDescriptor.toUpperCase().includes(flag));
  if (matchedFlag) {
    rules.push({ level: "elevated", title: "Descriptor keyword", detail: `Matched ${matchedFlag}` });
  }

  const hasCritical = rules.some((rule) => rule.level === "critical");
  const hasElevated = rules.some((rule) => rule.level === "elevated");
  return {
    rules,
    status: hasCritical ? "critical" : hasElevated ? "elevated" : "routine",
    integrity: hasCritical ? "Recalibration required" : hasElevated ? "Discordant" : "Validated",
  };
}

async function sha256(text) {
  if (!globalThis.crypto?.subtle) return "Unavailable";
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("").slice(0, 24);
}

function renderRules(rules) {
  if (!rules.length) {
    ruleList.innerHTML = '<div class="empty-state"><strong>No rules triggered</strong><span>All configured demonstration checks are within their nominal state.</span></div>';
    return;
  }
  ruleList.innerHTML = rules
    .map(
      (rule) => `
        <div class="rule-row ${rule.level}">
          <span class="rule-dot" aria-hidden="true"></span>
          <div><strong>${rule.title}</strong><span>${rule.detail}</span></div>
        </div>`,
    )
    .join("");
}

async function runEvaluation() {
  const payload = readInput();
  if (!payload.taskId || !payload.targetId || !Number.isFinite(payload.primaryMetric) || !Number.isFinite(payload.secondaryMetric)) {
    return;
  }
  const result = evaluate(payload);
  const labels = { routine: "Routine", elevated: "Elevated", critical: "Critical" };
  statusChip.className = `status-chip ${result.status}`;
  statusChip.textContent = labels[result.status];
  alertCount.textContent = String(result.rules.length);
  integrityState.textContent = result.integrity;
  renderRules(result.rules);
  fingerprint.textContent = await sha256(JSON.stringify(payload));
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runEvaluation();
});

resetButton.addEventListener("click", () => {
  form.reset();
  document.querySelector("#task-id").value = "TASK-001";
  document.querySelector("#target-id").value = "TARGET-01";
  document.querySelector("#primary-metric").value = "28.4";
  document.querySelector("#secondary-metric").value = "14.2";
  document.querySelector("#status-descriptor").value = "DISCORDANT";
  runEvaluation();
});

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("critic-theme", theme);
  themeToggle.setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} theme`);
}

themeToggle.addEventListener("click", () => {
  const current = document.documentElement.dataset.theme || "light";
  applyTheme(current === "dark" ? "light" : "dark");
});

const savedTheme = localStorage.getItem("critic-theme");
const preferredTheme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
applyTheme(savedTheme || preferredTheme);
runEvaluation();
