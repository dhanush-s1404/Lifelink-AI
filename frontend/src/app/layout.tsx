import type { Metadata } from "next";

import { Providers } from "./providers";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: {
    default: "LifeLink AI",
    template: "%s · LifeLink AI",
  },
  description:
    "A secure digital emergency vault for your family's most important information.",
};

const themeScript = `
(function () {
  try {
    var stored = localStorage.getItem("lifelink-theme");
    var dark = stored === "dark" || (stored === null && window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.toggle("dark", dark);
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased dark:bg-night-950 dark:text-slate-100">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}