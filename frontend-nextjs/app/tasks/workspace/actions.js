"use server";

const DEFAULT_API_BASE_URL = process.env.PWR_API_BASE_URL || "http://127.0.0.1:8000";

export async function createWorkspaceTaskAction(payload) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}/api/tasks`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      project_id: Number(payload.projectId),
      title: payload.title,
      description: "",
      task_type: "Pensar",
      context: payload.prompt || "",
      preferred_model: payload.model || "",
    }),
  });

  const body = await response.json().catch(() => ({
    error: "Backend returned an invalid JSON payload.",
  }));

  if (!response.ok) {
    throw new Error(body.detail || body.error || "Workspace task creation failed.");
  }

  return body;
}

export async function saveWorkspaceResultAction(payload) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}/api/tasks/${payload.taskId}/manual-result`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: payload.model,
      prompt: payload.prompt || "",
      result_text: payload.resultText || "",
    }),
  });

  const body = await response.json().catch(() => ({
    error: "Backend returned an invalid JSON payload.",
  }));

  if (!response.ok) {
    throw new Error(body.detail || body.error || "Workspace result save failed.");
  }

  return body;
}
