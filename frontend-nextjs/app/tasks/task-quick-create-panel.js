"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState, useTransition } from "react";

import { createTaskAction } from "./actions";

export default function TaskQuickCreatePanel({ projects }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [projectId, setProjectId] = useState(String(projects[0]?.id || ""));
  const [title, setTitle] = useState("");
  const [context, setContext] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const projectOptions = useMemo(
    () => projects.map((project) => ({ value: String(project.id), label: project.name })),
    [projects],
  );

  function handleCreate() {
    if (!projectId) {
      setErrorMessage("Selecciona un proyecto antes de crear la tarea.");
      return;
    }

    if (!String(title || "").trim()) {
      setErrorMessage("La tarea necesita un titulo breve.");
      return;
    }

    setErrorMessage("");

    startTransition(async () => {
      try {
        const createdTask = await createTaskAction({
          projectId: Number(projectId),
          title: String(title).trim(),
          description: "",
          taskType: "Pensar",
          context: String(context || "").trim(),
        });
        router.push(`/tasks/${createdTask.id}?created=1`);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No fue posible crear la tarea.");
      }
    });
  }

  return (
    <div className="panel">
      <div className="panel-body stack">
        <div className="band-head">
          <h2>Crear tarea</h2>
          <div className="subtle">Inicio rapido</div>
        </div>

        {projectOptions.length ? (
          <>
            <div className="form-field">
              <label htmlFor="quick-task-project">Proyecto</label>
              <select
                id="quick-task-project"
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
              >
                {projectOptions.map((project) => (
                  <option key={project.value} value={project.value}>
                    {project.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="quick-task-title">Titulo</label>
              <input
                id="quick-task-title"
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Que necesitas mover ahora"
              />
            </div>

            <div className="form-field">
              <label htmlFor="quick-task-context">Briefing</label>
              <textarea
                id="quick-task-context"
                rows={6}
                value={context}
                onChange={(event) => setContext(event.target.value)}
                placeholder="Contexto de trabajo para arrancar sin friccion"
              />
            </div>

            <div className="subtle">
              {isPending
                ? "Creando tarea y abriendo el detalle..."
                : "Se abrira el detalle de la tarea para ejecutarla o seguir trabajandola."}
            </div>

            <button className="primary-button" type="button" onClick={handleCreate} disabled={isPending}>
              {isPending ? "Creando..." : "Crear tarea"}
            </button>
          </>
        ) : (
          <div className="muted-box">Todavia no hay proyectos disponibles para crear tareas desde esta shell.</div>
        )}

        {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}
      </div>
    </div>
  );
}
