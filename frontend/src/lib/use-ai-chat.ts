"use client";

import { useCallback, useState } from "react";

import { ApiError, apiPost } from "@/lib/api";

export type ChatMessage = { id: string; role: "user" | "assistant"; content: string };

export function useAiChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (raw: string) => {
    const content = raw.trim();
    if (!content) return;

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content }]);
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
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isTyping, error, sendMessage, clear };
}