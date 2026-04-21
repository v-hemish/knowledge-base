"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Home, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/today", label: "Daily", title: "Today’s verse from the Gita", Icon: Home },
  { href: "/chat", label: "Reflect", title: "Ask something; answers cite this text", Icon: MessageCircle },
] as const;

export function PracticeLayoutClient({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-stone-50/80 via-white to-stone-50/50 text-[hsl(var(--foreground))]">
      <div className="flex-1 pb-[calc(4.5rem+env(safe-area-inset-bottom))]">{children}</div>
      <nav
        className="fixed bottom-0 left-0 right-0 z-40 border-t border-[hsl(var(--border))] bg-white/95 backdrop-blur-md"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
        aria-label="Gita Path"
      >
        <ul className="mx-auto flex max-w-lg items-stretch justify-around px-1 pt-1">
          {NAV.map(({ href, label, title, Icon }) => {
            const active = pathname === href;
            return (
              <li key={href} className="flex-1">
                <Link
                  href={href}
                  title={title}
                  className={cn(
                    "flex flex-col items-center gap-0.5 rounded-lg py-2 text-[11px] font-medium tracking-wide transition-colors",
                    active ? "gold-text" : "text-[hsl(var(--muted-foreground))] hover:text-stone-800",
                  )}
                >
                  <Icon className={cn("h-5 w-5", active && "stroke-[2.25px]")} strokeWidth={active ? 2.25 : 1.75} aria-hidden />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
