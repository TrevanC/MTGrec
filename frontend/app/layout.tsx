import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MTG EDH Upgrade Recommender",
  description: "Analyze your EDH/Commander deck and get upgrade recommendations based on synergy and statistics",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}