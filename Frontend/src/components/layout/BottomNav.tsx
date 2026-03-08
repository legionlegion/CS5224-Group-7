"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/map", label: "Map" },
  { href: "/log", label: "Log" },
  { href: "/leaderboard", label: "Rank" },
  { href: "/rewards", label: "Rewards" },
  { href: "/profile", label: "Profile" }
];

const hiddenRoutes = new Set(["/login", "/signup", "/complete-profile"]);

export function BottomNav() {
  const pathname = usePathname();

  if (hiddenRoutes.has(pathname)) {
    return null;
  }

  return (
    <nav className="fixed bottom-4 left-1/2 z-[1000] flex w-[calc(100%-2rem)] max-w-md -translate-x-1/2 justify-between rounded-full border border-white/60 bg-ink px-3 py-2 shadow-card backdrop-blur">
      {items.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              active ? "bg-leaf text-ink" : "text-white/80"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
