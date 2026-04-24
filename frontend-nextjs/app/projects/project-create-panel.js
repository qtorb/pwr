"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { createProjectAction } from "./actions";

export default function ProjectCreatePanel() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  function handleCreate() {
    if (!String(name || "").trim()) {
      setErrorMessage("El proyecto necesita un nombre claro.");
      return;
    }

    setErrorMessage("");

    startTransition(async () => {
      try {
        const project = await createProjectAction({
          name: String(name).trim(),
          description: String(description || "").trim(),
        });
        router.push(`/projects/${project.id}?created=1`);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No fue posible crear el proyecto.");
      }
    });
  }

  return (
    <div className="panel">
      <div className="panel-body stack">
        <div className="band-head">
          <h2>Crear proyecto</h2>
          <div className="subtle">Primero proyecto, luego tareas</div>
        </div>

        <div className="form-field">
          <label htmlFor="project-name">Nombre</label>
          <input
            id="project-name"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="PWR Dogfooding"
          />
        </div>

        <div className="form-field">
          <label htmlFor="project-description">Descripcion</label>
          <textarea
            id="project-description"
            rows={5}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Contexto breve para entender que contiene este proyecto."
          />
        </div>

        <div className="subtle">
          {isPending
            ? "Creando proyecto y abriendo su workspace..."
            : "El proyecto se abrira enseguida para crear la primera tarea dentro de su contexto."}
        </div>

        <button className="primary-button" type="button" onClick={handleCreate} disabled={isPending}>
          {isPending ? "Creando..." : "Crear proyecto"}
        </button>

        {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}
      </div>
    </div>
  );
}
