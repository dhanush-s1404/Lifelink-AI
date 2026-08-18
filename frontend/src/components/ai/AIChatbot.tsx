"use client";

import { ChatbotButton } from "@/components/ai/ChatbotButton";
import { ChatPanel } from "@/components/ai/ChatPanel";

export function AIChatbot() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <ChatbotButton onClick={() => setOpen(true)} />
      {open && <ChatPanel onClose={() => setOpen(false)} />}
    </>
  );
}