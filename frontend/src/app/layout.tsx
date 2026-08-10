import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    default: "LifeLink AI",
    template: "%s · LifeLink AI",
  },
  description:
    "A secure digital emergency vault for your family's most important information.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}
