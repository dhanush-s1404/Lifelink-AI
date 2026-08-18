"use client";

import { X } from "lucide-react";
import { useState } from "react";

export function ChatPanel({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<
    { id: string; role: "user" | "assistant"; content: string }[]
  >([]);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage = { id: Date.now().toString(), role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage.content }),
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "AI service error");
      }

      const data = await res.json();
      setMessages((prev) => [...prev, { id: Date.now().toString(), role: "assistant", content: data.response }]);
    } catch (e: any) {
      setError(e.message || "Failed to get AI response");
    } finally {
      setIsTyping(false);
    }
  };

  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <div className="fixed top-6 right-6 z-50 w-80 flex flex-col h-screen bg-white shadow-2L rounded-lg overflow-hidden transition-all duration-300 ease-out transform md:max-w-lg">
      <div className="flex items-center justify-between border-b p-4 border-slate-200">
        <span className="text-sm font-medium text-slate-900">LifeLink AI</span>
        <button
          onClick={onClose}
          aria-label="Close AI assistant"
          className="p-1 rounded hover:bg-slate-100"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 flex flex-col overflow-y-auto p-4 gap-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex items-start gap-3",
              msg.role === "user"
                ? "justify-end"
                : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-lg px-3 py-2 text-sm",
                msg.role === "user"
                  ? "bg-brand-100 text-slate-900 self-end"
                  : "bg-slate-100 text-slate-900"
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-start gap-3">
            <div className="animate-pulse rounded-lg bg-slate-100 px-3 py-2 text-sm h-10 w-24">
              &
            </div>
            <span className="text-xs text-slate-500">LifeLink AI is thinking&#8230;</span>
          </div>
        )}

        {error && (
          <div className="mt-2 p-3 rounded-lg bg-red-100 text-red-800 text-sm">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-2 text-red-600 underline cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-slate-200 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask LifeLink AI..."
          disabled={isTyping}
          className="flex-1 rounded-lg px-3 py-2 border border-slate-300 focus:outline-none focus:border-brand-500"
        />
        <button
          onClick={sendMessage}
          disabled={isTyping || !input.trim()}
          className="rounded-lg px-4 py-2 bg-brand-600 text-white hover:bg-brand-700 font-medium disabled:opacity-50"
        >
          {isTyping ? "Sending…" : "Send"}
        </button>
      </div>
    </div>
  );
}