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

export async function getProjectsPageData() {
  const [health, projects] = await Promise.allSettled([fetchJson("/health"), fetchJson("/api/projects")]);

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    health: health.status === "fulfilled" ? health.value : null,
    projects: projects.status === "fulfilled" ? projects.value.items : [],
    errors: [health, projects]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "Unknown API error"),
  };
}

export async function getTasksPageData(projectId = null) {
  const params = new URLSearchParams({ limit: "100" });
  if (projectId) {
    params.set("project_id", String(projectId));
  }

  const [health, projects, tasks] = await Promise.allSettled([
    fetchJson("/health"),
    fetchJson("/api/projects"),
    fetchJson(`/api/tasks?${params.toString()}`),
  ]);

  const projectItems = projects.status === "fulfilled" ? projects.value.items : [];
  const selectedProject = projectId
    ? projectItems.find((project) => String(project.id) === String(projectId)) || null
    : null;

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    health: health.status === "fulfilled" ? health.value : null,
    projects: projectItems,
    tasks: tasks.status === "fulfilled" ? tasks.value.items : [],
    selectedProject,
    errors: [health, projects, tasks]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "Unknown API error"),
  };
}

export async function getTaskDetailData(taskId) {
  const task = await Promise.allSettled([fetchJson(`/api/tasks/${taskId}`)]).then((results) => results[0]);
  const taskError = task.status === "rejected" ? task.reason?.message || "Unknown API error" : "";
  const taskPayload = task.status === "fulfilled" ? task.value : null;
  const taskType = encodeURIComponent(taskPayload?.task_type || "generic");

  const [latestExecution, executions, recommendation] = await Promise.allSettled([
    fetchJson(`/api/tasks/${taskId}/executions/latest`),
    fetchJson(`/api/tasks/${taskId}/executions`),
    fetchJson(`/api/model-runs/best?task_type=${taskType}`),
  ]);

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    task: taskPayload,
    latestExecution:
      latestExecution.status === "fulfilled" ? latestExecution.value.item || null : null,
    executions: executions.status === "fulfilled" ? executions.value.items : [],
    recommendation:
      recommendation.status === "fulfilled" ? recommendation.value.recommended || null : null,
    missing: taskError.includes(": 404"),
    errors: [task, latestExecution, executions, recommendation]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "Unknown API error"),
  };
}

export async function getTaskWorkspaceData(taskId = null, projectId = null) {
  const [health, projects] = await Promise.allSettled([fetchJson("/health"), fetchJson("/api/projects")]);
  let taskData = null;
  if (taskId) {
    taskData = await getTaskDetailData(taskId);
  }

  const projectItems = projects.status === "fulfilled" ? projects.value.items : [];
  const selectedProject = taskData?.task?.project_id
    ? projectItems.find((project) => String(project.id) === String(taskData.task.project_id)) || null
    : projectId
      ? projectItems.find((project) => String(project.id) === String(projectId)) || null
      : projectItems[0] || null;

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    health: health.status === "fulfilled" ? health.value : null,
    projects: projectItems,
    selectedProject,
    taskData,
    errors: [
      ...[health, projects]
        .filter((result) => result.status === "rejected")
        .map((result) => result.reason?.message || "Unknown API error"),
      ...(taskData?.errors || []),
    ],
  };
}

export const getQuickTaskData = getTaskWorkspaceData;

export async function getModelObservatorySummaryData() {
  const summaryResponse = await fetchJson("/api/model-runs/summary?limit=50");
  const rows = Array.isArray(summaryResponse.summary) ? summaryResponse.summary : [];
  const ordered = [...rows].sort((a, b) => {
    const byConversion = Number(b.conversion_rate || 0) - Number(a.conversion_rate || 0);
    if (byConversion !== 0) return byConversion;
    const byReuse = Number(b.reuse_rate || 0) - Number(a.reuse_rate || 0);
    if (byReuse !== 0) return byReuse;
    return Number(b.total_runs || 0) - Number(a.total_runs || 0);
  });
  const taskTypes = [...new Set(ordered.map((row) => row.task_type).filter(Boolean))];
  const hintResults = await Promise.allSettled(
    taskTypes.map(async (taskType) => {
      const response = await fetchJson(`/api/model-runs/best?task_type=${encodeURIComponent(taskType)}`);
      return response.recommended || null;
    }),
  );
  const bestHints = hintResults
    .filter((result) => result.status === "fulfilled" && result.value)
    .map((result) => result.value)
    .sort((a, b) => {
      const byScore = Number(b.score || 0) - Number(a.score || 0);
      if (byScore !== 0) return byScore;
      return String(a.task_type || "").localeCompare(String(b.task_type || ""));
    });

  return {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    summary: ordered,
    bestHints,
    totalRuns: Number(summaryResponse.total_runs || 0),
  };
}

export async function reuseAssetToTask(projectId, assetId) {
  const reusePayload = await postJson(`/api/assets/${assetId}/reuse`, {});
  const createdTask = await postJson("/api/tasks", {
    project_id: Number(projectId),
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
