"use server";

const DEFAULT_API_BASE_URL = process.env.PWR_API_BASE_URL || "http://127.0.0.1:8000";

export async function createProjectAction(payload) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}/api/projects`, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: payload.name,
      description: payload.description || "",
      objective: payload.objective || "",
      base_context: payload.baseContext || "",
      base_instructions: payload.baseInstructions || "",
      tags: payload.tags || "",
    }),
  });

  const body = await response.json().catch(() => ({
    error: "Backend returned an invalid JSON payload.",
  }));

  if (!response.ok) {
    throw new Error(body.detail || body.error || "Project creation failed.");
  }

  return body;
}
