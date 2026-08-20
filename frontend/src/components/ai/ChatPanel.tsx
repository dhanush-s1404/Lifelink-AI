"use client";

import { Send, Sparkles, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { useAiChat, type ChatMessage } from "@/lib/use-ai-chat";
import { cn } from "@/lib/utils";

function Bubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
          isUser
            ? "rounded-br-md bg-brand-gradient text-white"
            : "rounded-bl-md border border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-700 dark:bg-night-950 dark:text-white"
        )}
      >
        {message.content}
      </div>
    </div>
  );
}

export function ChatPanel({ onClose }: { onClose: () => void }) {
  const { messages, isTyping, error, sendMessage, clear } = useAiChat();
  const [input, setInput] = useState("");

  const submit = () => {
    sendMessage(input);
    setInput("");
  };

  return (
    <div
      role="dialog"
      aria-label="LifeLink AI assistant"
      className="fixed bottom-24 right-6 z-50 flex h-[min(34rem,calc(100vh-7rem))] w-[min(24rem,calc(100vw-3rem))] animate-scale-in flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lifted dark:border-slate-700 dark:bg-night-900 md:w-96"
    >
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3.5 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-white">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-white">LifeLink AI</p>
            <p className="text-xs text-slate-400 dark:text-slate-500">Always scoped to your access</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button
              onClick={clear}
              className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-night-800"
            >
              Clear
            </button>
          )}
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-night-800 dark:hover:text-white"
            aria-label="Close AI assistant"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
            Ask me about your vault, documents, or emergency setup.
          </p>
        )}
        {messages.map((msg) => (
          <Bubble key={msg.id} message={msg} />
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-3.5 py-3 dark:border-slate-700 dark:bg-night-950">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 dark:bg-slate-500" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:100ms] dark:bg-slate-500" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:200ms] dark:bg-slate-500" />
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-3.5 py-2.5 text-sm text-red-800 dark:text-red-300">
            <span>{error}</span>
            <button onClick={clear} className="ml-2 font-medium underline">
              Dismiss
            </button>
          </div>
        )}
      </div>

      <form
        className="flex items-center gap-2 border-t border-slate-200 p-3 dark:border-slate-800"
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
        <Button
          type="submit"
          size="sm"
          disabled={isTyping || !input.trim()}
          icon={<Send className="h-4 w-4" aria-hidden="true" />}
        >
          Send
        </Button>
      </form>
    </div>
  );
}