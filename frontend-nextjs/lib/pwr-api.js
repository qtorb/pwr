const DEFAULT_API_BASE_URL = process.env.PWR_API_BASE_URL || "http://127.0.0.1:8000";

export async function fetchJson(path, options = {}) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
    ...options,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed for ${path}: ${response.status}`);
  }

  return response.json();
}

export async function postJson(path, payload) {
  return fetchJson(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function getShellHomeData() {
  const [health, activity, reentry, projects] = await Promise.allSettled([
    fetchJson("/health"),
    fetchJson("/api/home/activity?limit=6"),
    fetchJson("/api/home/reentry?limit=6"),
    fetchJson("/api/projects"),
  ]);

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    health: health.status === "fulfilled" ? health.value : null,
    activity: activity.status === "fulfilled" ? activity.value.items : [],
    reentry: reentry.status === "fulfilled" ? reentry.value.items : [],
    projects: projects.status === "fulfilled" ? projects.value.items : [],
    errors: [health, activity, reentry, projects]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "Unknown API error"),
  };
}

export async function getProjectWorkspaceData(projectId) {
  const [project, tasks, assets] = await Promise.allSettled([
    fetchJson(`/api/projects/${projectId}`),
    fetchJson(`/api/projects/${projectId}/tasks`),
    fetchJson(`/api/projects/${projectId}/assets`),
  ]);

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    project: project.status === "fulfilled" ? project.value : null,
    tasks: tasks.status === "fulfilled" ? tasks.value.items : [],
    assets: assets.status === "fulfilled" ? assets.value.items : [],
    errors: [project, tasks, assets]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "Unknown API error"),
  };
}

export async function getTaskDetailData(taskId) {
  const [task, latestExecution, executions] = await Promise.allSettled([
    fetchJson(`/api/tasks/${taskId}`),
    fetchJson(`/api/tasks/${taskId}/executions/latest`),
    fetchJson(`/api/tasks/${taskId}/executions`),
  ]);

  const taskError = task.status === "rejected" ? task.reason?.message || "Unknown API error" : "";

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    task: task.status === "fulfilled" ? task.value : null,
    latestExecution:
      latestExecution.status === "fulfilled" ? latestExecution.value.item || null : null,
    executions: executions.status === "fulfilled" ? executions.value.items : [],
    missing: taskError.includes(": 404"),
    errors: [task, latestExecution, executions]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "Unknown API error"),
  };
}

export async function getModelObservatorySummaryData() {
  const summary = await fetchJson("/api/model-runs/summary?limit=50");
  const rows = Array.isArray(summary.summary) ? summary.summary : [];
  const ordered = [...rows].sort((a, b) => {
    const byConversion = Number(b.conversion_rate || 0) - Number(a.conversion_rate || 0);
    if (byConversion !== 0) return byConversion;
    const byReuse = Number(b.reuse_rate || 0) - Number(a.reuse_rate || 0);
    if (byReuse !== 0) return byReuse;
    return Number(b.total_runs || 0) - Number(a.total_runs || 0);
  });

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    summary: ordered,
    totalRuns: Number(summary.total_runs || 0),
  };
}

export async function reuseAssetToTask(projectId, assetId) {
  const reusePayload = await postJson(`/api/assets/${assetId}/reuse`, {});
  const createdTask = await postJson(`/api/projects/${projectId}/tasks`, {
    title: reusePayload.title || "Nueva tarea",
    description: reusePayload.notice || "",
    task_type: "Pensar",
    context: reusePayload.context || "",
  });

  return {
    reusePayload,
    createdTask,
  };
}
