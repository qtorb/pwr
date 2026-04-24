const DEFAULT_API_BASE_URL = process.env.PWR_API_BASE_URL || "http://127.0.0.1:8000";

async function fetchJson(path) {
  const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed for ${path}: ${response.status}`);
  }

  return response.json();
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
