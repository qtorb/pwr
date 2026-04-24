"use client";

import { useState, useTransition } from "react";

import { submitModelFeedbackAction } from "./actions";

const FEEDBACK_OPTIONS = [
  { value: "useful", label: "👍 util" },
  { value: "not_useful", label: "👎 no util" },
  { value: "used_other", label: "↔ use otro modelo" },
];

function confidenceCopy(value) {
  return {
    low: "baja",
    medium: "media",
    high: "alta",
  }[String(value || "").toLowerCase()] || "desconocida";
}

export default function TaskHintFeedback({ taskId, taskType, recommendation }) {
  const [isPending, startTransition] = useTransition();
  const [selectedFeedback, setSelectedFeedback] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [savedMessage, setSavedMessage] = useState("");

  if (!recommendation) return null;

  function handleFeedback(feedback) {
    if (isPending || selectedFeedback) return;

    setErrorMessage("");
    setSavedMessage("");

    startTransition(async () => {
      try {
        await submitModelFeedbackAction({
          taskId,
          taskType: recommendation.task_type || taskType || "generic",
          provider: recommendation.provider || "",
          model: recommendation.model || "",
          score: Number(recommendation.score || 0),
          confidence: recommendation.confidence || "",
          feedback,
        });
        setSelectedFeedback(feedback);
        setSavedMessage("feedback guardado");
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No fue posible guardar el feedback.");
      }
    });
  }

  return (
    <section className="hint-callout">
      <div className="hint-label">Hint experimental</div>
      <div className="hint-title">{recommendation.model || "Modelo sugerido"}</div>
      <div className="hint-meta">
        <span>Confianza {confidenceCopy(recommendation.confidence)}</span>
        <span>{recommendation.total_runs || 0} ejecuciones observadas</span>
        {recommendation.provider ? <span>{recommendation.provider}</span> : null}
      </div>
      {recommendation.reason ? <div className="subtle">{recommendation.reason}</div> : null}

      <div className="hint-feedback-row">
        {FEEDBACK_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`feedback-chip${selectedFeedback === option.value ? " active" : ""}`}
            onClick={() => handleFeedback(option.value)}
            disabled={isPending || Boolean(selectedFeedback)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {savedMessage ? <div className="subtle">{savedMessage}</div> : null}
      {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}
    </section>
  );
}
