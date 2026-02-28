"use client";

import { FormEvent, useMemo, useState } from "react";

import { ApiError, sendChat } from "@/lib/api";
import type { ChatResponse, ChatScope } from "@/lib/types";

type ScopeChatPanelProps = {
  title: string;
  subtitle?: string;
  defaultScope: ChatScope;
  lockedProjectName?: string;
};

export default function ScopeChatPanel({
  title,
  subtitle,
  defaultScope,
  lockedProjectName,
}: ScopeChatPanelProps) {
  const [scope, setScope] = useState<ChatScope>(defaultScope);
  const [projectName, setProjectName] = useState(lockedProjectName ?? "");
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(4);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);

  const effectiveScope = lockedProjectName ? "project" : scope;
  const requiresProject = effectiveScope === "project";
  const safeTopK = useMemo(() => Math.min(10, Math.max(1, topK || 1)), [topK]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!query.trim()) {
      setError("Please enter a query.");
      return;
    }
    if (requiresProject && !projectName.trim()) {
      setError("Project name is required for project scope.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await sendChat({
        query: query.trim(),
        scope: effectiveScope,
        top_k: safeTopK,
        project_name: requiresProject ? projectName.trim() : undefined,
      });
      setResult(response);
    } catch (chatError) {
      if (chatError instanceof ApiError) {
        setError(chatError.detail);
      } else {
        setError("Chat request failed due to an unknown error.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <h2 className="panel-title">{title}</h2>
      {subtitle && <p className="panel-subtitle">{subtitle}</p>}

      <form onSubmit={handleSubmit} className="field-group" style={{ marginTop: "0.9rem" }}>
        {!lockedProjectName && (
          <div className="field">
            <label htmlFor={`${title}-scope`}>Scope</label>
            <select
              id={`${title}-scope`}
              value={scope}
              onChange={(event) => setScope(event.target.value as ChatScope)}
            >
              <option value="project">project</option>
              <option value="realestate_global">realestate_global</option>
              <option value="global">global</option>
            </select>
          </div>
        )}

        {requiresProject && (
          <div className="field">
            <label htmlFor={`${title}-projectName`}>Project Name</label>
            <input
              id={`${title}-projectName`}
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              placeholder="Project name"
              disabled={Boolean(lockedProjectName)}
            />
          </div>
        )}

        <div className="field">
          <label htmlFor={`${title}-topK`}>Top K</label>
          <input
            id={`${title}-topK`}
            type="number"
            min={1}
            max={10}
            value={topK}
            onChange={(event) => setTopK(Number(event.target.value))}
          />
        </div>

        <div className="field">
          <label htmlFor={`${title}-query`}>Query</label>
          <textarea
            id={`${title}-query`}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask for risks, KPIs, missing data, comparables..."
          />
        </div>

        <div className="actions">
          <button type="submit" className="button" disabled={isSubmitting}>
            {isSubmitting ? "Thinking..." : "Run Chat"}
          </button>
        </div>

        {error && <div className="status-error">{error}</div>}
      </form>

      {result && (
        <div style={{ marginTop: "1rem" }}>
          <div className="actions" style={{ marginBottom: "0.6rem" }}>
            <span className="tag">scope: {result.scope}</span>
            <span className="tag">effective: {result.effective_scope}</span>
            <span className="tag">evidence: {result.evidence.length}</span>
          </div>

          <div className="answer-box">{result.answer}</div>

          {result.evidence.length > 0 && (
            <div className="evidence-list">
              {result.evidence.map((item, index) => (
                <div className="evidence-item" key={`${item.source}-${index}`}>
                  <div className="evidence-head">
                    <span>{item.source}</span>
                    <span>{item.score === null ? "score n/a" : `score ${item.score.toFixed(3)}`}</span>
                  </div>
                  <div className="evidence-text">{item.excerpt}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
