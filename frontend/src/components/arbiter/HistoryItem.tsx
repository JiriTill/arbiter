"use client";

import { Gamepad2, ChevronRight, CheckCircle, AlertTriangle, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { type HistoryEntry, type Confidence, formatRelativeTime } from "@/lib/mock-history";

interface HistoryItemProps {
    entry: HistoryEntry;
    onClick: () => void;
    className?: string;
}

const confidenceBadge: Record<Confidence, { icon: React.ElementType; color: string; bgColor: string; borderColor: string }> = {
    high: {
        icon: CheckCircle,
        color: "text-emerald-400",
        bgColor: "bg-emerald-500/10",
        borderColor: "border-emerald-500/20",
    },
    medium: {
        icon: AlertTriangle,
        color: "text-amber-400",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/20",
    },
    low: {
        icon: HelpCircle,
        color: "text-amber-400",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/20",
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
                "flex w-full items-start gap-4 p-4 text-left group",
                "transition-all duration-200",
                "hover:bg-muted/30 hover:border-emerald-500/30 active:scale-[0.99]",
                "border-b border-border last:border-b-0",
                "min-h-[80px]", // Good tap target
                className
            )}
        >
            {/* Game Icon */}
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-muted to-muted/50 border border-border/50 mt-0.5 group-hover:border-emerald-500/30 transition-colors">
                <Gamepad2 className="h-5 w-5 text-muted-foreground group-hover:text-emerald-400 transition-colors" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 space-y-2">
                {/* Game + Edition + Timestamp */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-medium text-foreground/90">{entry.gameName}</span>
                    {entry.gameEdition && (
                        <>
                            <span className="hidden sm:inline opacity-50">•</span>
                            <span className="hidden sm:inline opacity-70">{entry.gameEdition}</span>
                        </>
                    )}
                    <span className="ml-auto shrink-0 font-medium">{formatRelativeTime(entry.timestamp)}</span>
                </div>

                {/* Question (truncated to 2 lines) */}
                <p className="text-sm font-medium leading-snug line-clamp-2 text-foreground/90 group-hover:text-emerald-400 transition-colors">
                    {entry.question}
                </p>

                {/* Verdict Snippet & Badge */}
                <div className="flex items-center gap-3 pt-1">
                    <div
                        className={cn(
                            "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium border",
                            badge.bgColor,
                            badge.color,
                            badge.borderColor
                        )}
                    >
                        <BadgeIcon className="h-3 w-3" />
                        <span className="capitalize">{entry.confidence}</span>
                    </div>

                    <p className="text-xs text-muted-foreground truncate flex-1">
                        {entry.verdict}
                    </p>
                </div>
            </div>

            {/* Arrow */}
            <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground/30 mt-4 group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-all" />
        </button>
    );
}
