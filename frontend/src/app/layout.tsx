import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentHive — Collaborative AI Agent Platform",
  description: "The Operating Network for Autonomous & Semi-Autonomous AI Agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen antialiased selection:bg-amber-500 selection:text-black">
        {children}
      </body>
    </html>
  );
}
