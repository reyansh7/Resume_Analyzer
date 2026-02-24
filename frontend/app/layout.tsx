import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/app/providers";
import { AnimatedBackground } from "@/components/animated-background";

export const metadata: Metadata = {
  title: "Resume Analyzer AI",
  description: "Premium AI-powered resume and skill gap analyzer",
  icons: {
    icon: "/icon.svg"
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>
          <AnimatedBackground />
          {children}
        </Providers>
      </body>
    </html>
  );
}
