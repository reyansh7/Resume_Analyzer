import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-white/30 bg-white/50 backdrop-blur-xl dark:bg-black/20">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-3 py-3 sm:px-4">
        <Link href="/" className="max-w-[58vw] truncate text-sm font-semibold tracking-tight sm:max-w-none sm:text-lg">
          Resume Analyzer AI
        </Link>
        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggle />
          <Link href="/login">
            <Button className="px-3 text-xs sm:px-4 sm:text-sm">Get Started</Button>
          </Link>
        </div>
      </nav>
    </header>
  );
}
