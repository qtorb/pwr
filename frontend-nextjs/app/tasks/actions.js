"use server";

const DEFAULT_API_BASE_URL = process.env.PWR_API_BASE_URL || "http://127.0.0.1:8000";

export async function createTaskAction(payload) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}/api/projects/${payload.projectId}/tasks`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: payload.title,
      description: payload.description || "",
      task_type: payload.taskType || "Pensar",
      context: payload.context || "",
    }),
  });

  const body = await response.json().catch(() => ({
    error: "Backend returned an invalid JSON payload.",
  }));

  if (!response.ok) {
    throw new Error(body.detail || body.error || "Task creation failed.");
  }

  return body;
}
