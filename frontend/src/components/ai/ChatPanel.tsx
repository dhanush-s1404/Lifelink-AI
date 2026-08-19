"use client";

import { cn } from "@/lib/utils";
import { useState } from "react";
import { Sparkles, X } from "lucide-react";
import { ApiError, apiPost } from "@/lib/api";

type ChatMessage = { id: string; role: "user" | "assistant"; content: string };

export function ChatPanel({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async () => {
    const content = input.trim();
    if (!content || isTyping) return;

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content };
    setMessages((prev) => [...prev, userMessage]);
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

  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <div
      role="dialog"
      aria-label="LifeLink AI assistant"
      className="fixed bottom-24 right-6 z-50 flex h-[min(32rem,calc(100vh-7rem))] w-[min(24rem,calc(100vw-3rem))] flex-col overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-night-900 shadow-xl md:w-96"
    >
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden="true" />
          <span className="text-sm font-medium text-slate-900 dark:text-white">LifeLink AI</span>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button
              onClick={clearConversation}
              className="rounded px-2 py-1 text-xs text-slate-500 dark:text-slate-400 transition hover:bg-slate-100 dark:hover:bg-night-800"
            >
              Clear
            </button>
          )}
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-500 dark:text-slate-400 transition hover:bg-slate-100 dark:hover:bg-night-800"
            aria-label="Close AI assistant"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Ask me about your vault, documents, or emergency setup.
          </p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
          >
            <div
              className={cn(
                "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                msg.role === "user"
                  ? "bg-brand-600 text-white"
                  : "border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-night-950 text-slate-900 dark:text-white"
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-night-950 px-3 py-2">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:100ms]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:200ms]" />
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-3 py-2 text-sm text-red-800 dark:text-red-300">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-2 font-medium underline">
              Dismiss
            </button>
          </div>
        )}
      </div>

      <form
        className="flex items-center gap-2 border-t border-slate-200 dark:border-slate-800 p-3"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask LifeLink AI…"
          disabled={isTyping}
          aria-label="Message"
          className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-900 dark:text-white shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isTyping || !input.trim()}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isTyping ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}