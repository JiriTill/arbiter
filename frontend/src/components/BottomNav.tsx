"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageCircleQuestion, History, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    href: "/ask",
    label: "Ask",
    icon: <MessageCircleQuestion className="h-6 w-6" />,
  },
  {
    href: "/history",
    label: "History",
    icon: <History className="h-6 w-6" />,
  },
  {
    href: "/profile",
    label: "Profile",
    icon: <User className="h-6 w-6" />,
  },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex h-16 max-w-md items-center justify-around px-4 pb-safe">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href === "/ask" && pathname === "/");
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center gap-1 px-3 py-2 text-xs font-medium transition-colors",
                isActive
                  ? "text-[#4ade80]"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
