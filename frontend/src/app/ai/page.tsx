"use client";

import { Send, Sparkles } from "lucide-react";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAiChat, type ChatMessage } from "@/lib/use-ai-chat";
import { cn } from "@/lib/utils";

const suggestions = [
  "What should I store in my vault?",
  "How does emergency access work?",
  "Who can see my information?",
];

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "rounded-br-md bg-brand-gradient text-white shadow-card"
            : "rounded-bl-md border border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-700 dark:bg-night-950 dark:text-white"
        )}
      >
        {message.content}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-night-950">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 dark:bg-slate-500" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:100ms] dark:bg-slate-500" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:200ms] dark:bg-slate-500" />
      </div>
    </div>
  );
}

export default function AiAssistantPage() {
  const { messages, isTyping, error, sendMessage, clear } = useAiChat();
  const [input, setInput] = useState("");

  const submit = () => {
    sendMessage(input);
    setInput("");
  };

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="page-heading-icon">
                <Sparkles className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <h1 className="page-heading">AI assistant</h1>
                <p className="page-subheading">
                  Ask questions about your vault and emergency setup. Answers are scoped to what
                  you can access.
                </p>
              </div>
            </div>
            {messages.length > 0 && (
              <Button variant="ghost" size="sm" onClick={clear}>
                Clear conversation
              </Button>
            )}
          </div>

          <Card className="mt-6 flex h-[calc(100vh-16rem)] min-h-[28rem] flex-col overflow-hidden">
            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {messages.length === 0 && (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-glow">
                    <Sparkles className="h-7 w-7" aria-hidden="true" />
                  </span>
                  <p className="mt-5 text-sm font-medium text-slate-700 dark:text-slate-200">
                    Start a conversation
                  </p>
                  <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
                    Ask about your vault, emergency access, or security — everything is scoped to
                    your account.
                  </p>
                  <div className="mt-6 flex flex-col gap-2">
                    {suggestions.map((s) => (
                      <button
                        key={s}
                        onClick={() => {
                          sendMessage(s);
                          setInput("");
                        }}
                        className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-soft dark:border-slate-700 dark:bg-night-900 dark:text-slate-200 dark:hover:border-brand-700"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}

              {isTyping && <TypingIndicator />}

              {error && (
                <div className="alert alert-error">
                  <div className="flex-1">
                    <span>{error}</span>
                  </div>
                  <button onClick={() => clear()} className="shrink-0 font-medium underline">
                    Dismiss
                  </button>
                </div>
              )}
            </div>

            <form
              className="flex items-center gap-3 border-t border-slate-200 p-4 dark:border-slate-800"
              onSubmit={(e) => {
                e.preventDefault();
                submit();
              }}
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask LifeLink AI…"
                disabled={isTyping}
                aria-label="Message"
                className="form-control flex-1"
              />
              <Button type="submit" disabled={isTyping || !input.trim()} icon={<Send className="h-4 w-4" aria-hidden="true" />}>
                Send
              </Button>
            </form>
          </Card>
        </div>
      </AppShell>
    </RequireAuth>
  );
}