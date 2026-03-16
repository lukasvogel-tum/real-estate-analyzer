"use client";

import { FormEvent, useMemo, useState } from "react";
import { FileText, Loader2, MessageSquare, SearchCheck } from "lucide-react";

import ConfirmDialog from "@/components/app/confirm-dialog";
import EmptyState from "@/components/app/empty-state";
import SectionCard from "@/components/app/section-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, sendChat } from "@/lib/api";
import type { ChatResponse, ChatScope } from "@/lib/types";

type ScopeChatPanelProps = {
  title: string;
  subtitle?: string;
  defaultScope: ChatScope;
  lockedProjectName?: string;
  lockScope?: boolean;
  layoutVariant?: "default" | "hero";
  queryPlaceholder?: string;
  submitLabel?: string;
};

function ResultView({ result }: { result: ChatResponse }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">scope: {result.scope}</Badge>
        <Badge variant="outline">effective: {result.effective_scope}</Badge>
        <Badge variant="secondary">evidence: {result.evidence.length}</Badge>
      </div>

      <Tabs defaultValue="answer">
        <TabsList>
          <TabsTrigger value="answer">Answer</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          {result.graph_facts && result.graph_facts.length > 0 ? (
            <TabsTrigger value="graph">Graph</TabsTrigger>
          ) : null}
        </TabsList>
        <TabsContent value="answer" className="space-y-2">
          <div className="rounded-md border border-border bg-muted/20 p-4 text-sm leading-6 text-foreground">
            {result.answer}
          </div>
        </TabsContent>
        <TabsContent value="evidence">
          {result.evidence.length === 0 ? (
            <EmptyState
              title="No evidence snippets"
              description="The model returned an answer but no evidence snippets for this query."
              icon={FileText}
            />
          ) : (
            <ul className="space-y-3">
              {result.evidence.map((item, index) => (
                <li
                  key={`${item.source}-${index}`}
                  className="rounded-md border border-border bg-background p-3"
                >
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-medium text-foreground">{item.source}</span>
                    {item.score === null ? (
                      <Badge variant="outline">score n/a</Badge>
                    ) : (
                      <Badge variant="outline">score {item.score.toFixed(3)}</Badge>
                    )}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-foreground/90">{item.excerpt}</p>
                </li>
              ))}
            </ul>
          )}
        </TabsContent>
        {result.graph_facts && result.graph_facts.length > 0 ? (
          <TabsContent value="graph">
            <ul className="space-y-3">
              {result.graph_facts.map((fact, index) => (
                <li
                  key={`${fact.kind}-${fact.label ?? "fact"}-${index}`}
                  className="rounded-md border border-border bg-background p-3"
                >
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline">{fact.kind}</Badge>
                    {fact.label ? (
                      <span className="font-medium text-foreground">{fact.label}</span>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-foreground/90">{fact.text}</p>
                </li>
              ))}
            </ul>
          </TabsContent>
        ) : null}
      </Tabs>
    </div>
  );
}

export default function ScopeChatPanel({
  title,
  subtitle,
  defaultScope,
  lockedProjectName,
  lockScope = false,
  layoutVariant = "default",
  queryPlaceholder = "Ask for risks, cashflow assumptions, missing data, or decision support.",
  submitLabel = "Run Chat",
}: ScopeChatPanelProps) {
  const [scope, setScope] = useState<ChatScope>(defaultScope);
  const [projectName, setProjectName] = useState(lockedProjectName ?? "");
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState("4");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const panelId = useMemo(
    () => title.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
    [title],
  );

  const effectiveScope = lockedProjectName ? "project" : scope;
  const requiresProject = effectiveScope === "project";
  const parsedTopK = Number.parseInt(topK, 10);
  const safeTopK = useMemo(() => {
    if (Number.isNaN(parsedTopK)) {
      return 4;
    }
    return Math.min(10, Math.max(1, parsedTopK));
  }, [parsedTopK]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
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
        query: trimmedQuery,
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

  function clearResult() {
    setError("");
    setResult(null);
    setQuery("");
  }

  const formFields = (
    <>
      {!lockedProjectName && !lockScope ? (
        <div className="space-y-2">
          <Label htmlFor={`${panelId}-scope`}>Scope</Label>
          <Select value={scope} onValueChange={(value) => setScope(value as ChatScope)}>
            <SelectTrigger id={`${panelId}-scope`} aria-label="Chat scope">
              <SelectValue placeholder="Select scope" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="project">project</SelectItem>
              <SelectItem value="realestate_global">realestate_global</SelectItem>
              <SelectItem value="global">global</SelectItem>
            </SelectContent>
          </Select>
        </div>
      ) : null}

      {requiresProject ? (
        <div className="space-y-2">
          <Label htmlFor={`${panelId}-projectName`}>Project Name</Label>
          <Input
            id={`${panelId}-projectName`}
            value={projectName}
            onChange={(event) => setProjectName(event.target.value)}
            placeholder="Project name"
            disabled={Boolean(lockedProjectName)}
            autoComplete="off"
          />
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
        <div className="space-y-2">
          <Label htmlFor={`${panelId}-topK`}>Top K</Label>
          <Input
            id={`${panelId}-topK`}
            type="number"
            min={1}
            max={10}
            value={topK}
            onChange={(event) => setTopK(event.target.value)}
            inputMode="numeric"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${panelId}-query`}>Query</Label>
          <Textarea
            id={`${panelId}-query`}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={queryPlaceholder}
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              Thinking...
            </>
          ) : (
            <>
              <SearchCheck className="h-4 w-4" aria-hidden="true" />
              {submitLabel}
            </>
          )}
        </Button>
        <ConfirmDialog
          triggerLabel="Clear"
          title="Clear chat output?"
          description="This removes the current answer and resets your query field."
          confirmLabel="Clear"
          onConfirm={clearResult}
          triggerVariant="outline"
        />
      </div>

      {error ? (
        <p
          className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          aria-live="polite"
        >
          {error}
        </p>
      ) : null}
    </>
  );

  const resultState = (
    <>
      {isSubmitting ? (
        <div className="rounded-md border border-border bg-muted/30 px-4 py-8 text-center text-sm text-muted-foreground">
          Generating answer from indexed context...
        </div>
      ) : null}

      {!isSubmitting && !result ? (
        <EmptyState
          title="No answer yet"
          description="Submit a query to generate a grounded response with evidence excerpts."
          icon={MessageSquare}
        />
      ) : null}

      {result ? <ResultView result={result} /> : null}
    </>
  );

  if (layoutVariant === "hero") {
    return (
      <div className="rounded-[28px] border border-border/70 bg-card/80 shadow-soft">
        <div className="border-b border-border/70 px-6 py-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold text-foreground">{title}</h2>
              {subtitle ? (
                <p className="max-w-3xl text-sm text-muted-foreground">{subtitle}</p>
              ) : null}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">scope: {effectiveScope}</Badge>
              <Badge variant="secondary">top k: {safeTopK}</Badge>
            </div>
          </div>
        </div>

        <div className="space-y-6 p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {formFields}
          </form>
          {resultState}
        </div>
      </div>
    );
  }

  return (
    <SectionCard title={title} description={subtitle}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {formFields}
      </form>
      {resultState}
    </SectionCard>
  );
}
