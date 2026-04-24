"use server";

const DEFAULT_API_BASE_URL = process.env.PWR_API_BASE_URL || "http://127.0.0.1:8000";

export async function executeTaskAction(taskId) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}/api/tasks/${taskId}/execute`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
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
