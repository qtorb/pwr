import { redirect } from "next/navigation";

export default async function QuickTaskPage({ searchParams }) {
  const resolvedSearchParams = (await searchParams) || {};
  const params = new URLSearchParams();

  if (resolvedSearchParams.taskId) params.set("taskId", resolvedSearchParams.taskId);
  if (resolvedSearchParams.projectId) params.set("projectId", resolvedSearchParams.projectId);
  if (resolvedSearchParams.created) params.set("created", resolvedSearchParams.created);
  if (resolvedSearchParams.saved) params.set("saved", resolvedSearchParams.saved);

  redirect(`/tasks/workspace${params.size ? `?${params.toString()}` : ""}`);
}
