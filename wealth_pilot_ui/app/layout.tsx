import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WealthPilot — AI Wealth Advisor",
  description: "AI-powered stock analysis and portfolio management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
