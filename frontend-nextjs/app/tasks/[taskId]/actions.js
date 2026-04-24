"use server";

const DEFAULT_API_BASE_URL = process.env.PWR_API_BASE_URL || "http://127.0.0.1:8000";

export async function executeTaskAction(taskId) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}/api/tasks/${taskId}/execute`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "X-PWR-Source-App": "PWR-Web",
    },
  });

  const payload = await response.json().catch(() => ({
    error: "Backend returned an invalid JSON payload.",
  }));

  if (!response.ok) {
    throw new Error(payload.detail || payload.error || "Task execution failed.");
  }

  return payload;
}

export async function saveAssetAction(payload) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}/api/projects/${payload.projectId}/assets`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      task_id: payload.taskId,
      source_execution_id: payload.sourceExecutionId,
      source_execution_status: payload.sourceExecutionStatus,
      asset_type: payload.assetType,
      title: payload.title,
      summary: payload.summary,
      content: payload.content,
    }),
  });

  const body = await response.json().catch(() => ({
    error: "Backend returned an invalid JSON payload.",
  }));

  if (!response.ok) {
    throw new Error(body.detail || body.error || "Asset creation failed.");
  }

  return body;
}
