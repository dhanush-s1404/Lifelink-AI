"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";

export function ChatbotButton() {
  const [expanded, setExpanded] = useState(false);

  return (
    <button
      onClick={() => setExpanded(!expanded)}
      aria-label={expanded ? "Collapse AI assistant" : "Expand AI assistant"}
      className="fixed bottom-6 right-6 z-50 rounded-full bg-brand-600 p-2.5 hover:bg-brand-700 transition-colors"
    >
      <Sparkles className="h-6 w-6 text-white" />
    </button>
  );
}