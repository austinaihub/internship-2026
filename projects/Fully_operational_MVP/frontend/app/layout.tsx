import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AustinAIHub Content Creator",
  description: "Human Trafficking Awareness Content Creator by AustinAIHub",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head suppressHydrationWarning>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet" />
        <script src="https://unpkg.com/@tailwindcss/browser@4" suppressHydrationWarning></script>
        <style type="text/tailwindcss" dangerouslySetInnerHTML={{ __html: `
          @theme {
            --color-primary: #8b5cf6;
            --color-secondary: #06b6d4;
            --color-accent: #10b981;
            --font-sans: "Inter", sans-serif;
            --font-mono: "JetBrains Mono", monospace;
          }
        ` }} suppressHydrationWarning />
      </head>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
