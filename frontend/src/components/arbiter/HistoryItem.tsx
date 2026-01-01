"use client";

import { Gamepad2, ChevronRight, CheckCircle, AlertTriangle, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { type HistoryEntry, type Confidence, formatRelativeTime } from "@/lib/mock-history";

interface HistoryItemProps {
    entry: HistoryEntry;
    onClick: () => void;
    className?: string;
}

const confidenceBadge: Record<Confidence, { icon: React.ElementType; color: string; bgColor: string }> = {
    high: {
        icon: CheckCircle,
        color: "text-[#4ade80]",
        bgColor: "bg-[#4ade80]/10",
    },
    medium: {
        icon: AlertTriangle,
        color: "text-[#fbbf24]",
        bgColor: "bg-[#fbbf24]/10",
    },
    low: {
        icon: HelpCircle,
        color: "text-[#f87171]",
        bgColor: "bg-[#f87171]/10",
    },
};

export function HistoryItem({ entry, onClick, className }: HistoryItemProps) {
    const badge = confidenceBadge[entry.confidence];
    const BadgeIcon = badge.icon;

    return (
        <button
            type="button"
            onClick={onClick}
            className={cn(
                "flex w-full items-start gap-3 p-4 text-left",
                "transition-colors hover:bg-[#1a1a1a] active:bg-[#222222]",
                "border-b border-[#2a2a2a] last:border-b-0",
                "min-h-[72px]", // Good tap target
                className
            )}
        >
            {/* Game Icon */}
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted mt-0.5">
                <Gamepad2 className="h-5 w-5 text-muted-foreground" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 space-y-1.5">
                {/* Game + Edition + Timestamp */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-medium text-foreground/80">{entry.gameName}</span>
                    <span className="hidden sm:inline">•</span>
                    <span className="hidden sm:inline">{entry.gameEdition}</span>
                    <span className="ml-auto shrink-0">{formatRelativeTime(entry.timestamp)}</span>
                </div>

                {/* Question (truncated to 2 lines) */}
                <p className="text-sm font-medium leading-snug line-clamp-2">
                    {entry.question}
                </p>

                {/* Confidence Badge */}
                <div
                    className={cn(
                        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs",
                        badge.bgColor,
                        badge.color
                    )}
                >
                    <BadgeIcon className="h-3 w-3" />
                    <span className="capitalize">{entry.confidence}</span>
                </div>
            </div>

            {/* Arrow */}
            <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground mt-3" />
        </button>
    );
}
