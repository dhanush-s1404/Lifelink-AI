"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { ApiError, apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";

type ChatMessage = { id: string; role: "user" | "assistant"; content: string };

const suggestions = [
  "What should I store in my vault?",
  "How does emergency access work?",
  "Who can see my information?",
];

export default function AiAssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (text: string) => {
    const content = text.trim();
    if (!content || isTyping) return;

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content }]);
    setInput("");
    setIsTyping(true);
    setError(null);

    try {
      const data = await apiPost<{ response: string }>("/auth/ai/chat", { message: content });
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: data.response },
      ]);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to get an AI response.";
      setError(message);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
              <Sparkles className="h-5 w-5 text-brand-700" aria-hidden="true" />
            </span>
            <div>
              <h1 className="page-heading">AI assistant</h1>
              <p className="page-subheading">
                Ask questions about your vault and emergency setup. Answers are scoped to what
                you can access.
              </p>
            </div>
          </div>

          <Card className="mt-6 flex h-[calc(100vh-16rem)] min-h-[28rem] flex-col">
            <div className="flex-1 space-y-3 overflow-y-auto p-5">
              {messages.length === 0 && (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <Sparkles className="h-8 w-8 text-brand-200" aria-hidden="true" />
                  <p className="mt-3 text-sm text-slate-500">
                    Start a conversation. For example:
                  </p>
                  <div className="mt-4 flex flex-col gap-2">
                    {suggestions.map((s) => (
                      <button
                        key={s}
                        onClick={() => sendMessage(s)}
                        className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition hover:border-brand-300 hover:bg-brand-50"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <div key={msg.id} className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
                  <div
                    className={cn(
                      "max-w-[80%] whitespace-pre-wrap rounded-lg px-4 py-2.5 text-sm",
                      msg.role === "user"
                        ? "bg-brand-600 text-white"
                        : "border border-slate-200 bg-slate-50 text-slate-900"
                    )}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:100ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:200ms]" />
                  </div>
                </div>
              )}

              {error && (
                <div className="alert alert-error">
                  <span>{error}</span>
                  <button onClick={() => setError(null)} className="ml-2 font-medium underline">
                    Dismiss
                  </button>
                </div>
              )}
            </div>

            <form
              className="flex items-center gap-3 border-t border-slate-200 p-4"
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage(input);
              }}
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask LifeLink AI…"
                disabled={isTyping}
                aria-label="Message"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20 disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={isTyping || !input.trim()}
                className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </Card>
        </div>
      </AppShell>
    </RequireAuth>
  );
}