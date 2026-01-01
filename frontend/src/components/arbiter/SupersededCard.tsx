"use client";

import { useState, useRef, TouchEvent } from "react";
import { ChevronDown, AlertOctagon, FileText, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { SupersededRule } from "@/types/arbiter";

interface SupersededCardProps {
    supersededRule: SupersededRule;
    className?: string;
}

export function SupersededCard({
    supersededRule,
    className,
}: SupersededCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const touchStartY = useRef<number | null>(null);

    const { quote, page, reason, confidence } = supersededRule;

    // Handle swipe gesture for mobile
    const handleTouchStart = (e: TouchEvent<HTMLButtonElement>) => {
        touchStartY.current = e.touches[0].clientY;
    };

    const handleTouchEnd = (e: TouchEvent<HTMLButtonElement>) => {
        if (touchStartY.current === null) return;

        const touchEndY = e.changedTouches[0].clientY;
        const deltaY = touchStartY.current - touchEndY;

        // Swipe up to expand, swipe down to collapse
        if (Math.abs(deltaY) > 30) {
            if (deltaY > 0 && !isExpanded) {
                setIsExpanded(true);
            } else if (deltaY < 0 && isExpanded) {
                setIsExpanded(false);
            }
        }

        touchStartY.current = null;
    };

    return (
        <div
            className={cn(
                "rounded-lg border-2 border-amber-500/30 bg-amber-50/5 overflow-hidden",
                "dark:border-amber-600/30 dark:bg-amber-900/10",
                className
            )}
        >
            {/* Clickable/Swipeable Header */}
            <button
                type="button"
                onClick={() => setIsExpanded(!isExpanded)}
                onTouchStart={handleTouchStart}
                onTouchEnd={handleTouchEnd}
                className={cn(
                    "flex w-full items-center justify-between gap-3 p-4 text-left",
                    "transition-colors hover:bg-amber-500/10",
                    "min-h-[56px]" // Large tap target
                )}
            >
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/20">
                        <RefreshCw className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                        <span className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                            🔄 This overrides a base game rule
                        </span>
                        <p className="text-xs text-amber-600/80 dark:text-amber-400/80">
                            Tap to see the original rule
                        </p>
                    </div>
                </div>

                <ChevronDown
                    className={cn(
                        "h-5 w-5 text-amber-600 dark:text-amber-400 transition-transform duration-200",
                        isExpanded && "rotate-180"
                    )}
                />
            </button>

            {/* Expandable Content */}
            <div
                className={cn(
                    "grid transition-all duration-200 ease-out",
                    isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                )}
            >
                <div className="overflow-hidden">
                    <div className="border-t border-amber-500/20 p-4 pt-4">
                        {/* Old Quote */}
                        <div className="mb-4">
                            <div className="mb-2 flex items-center justify-between">
                                <span className="text-xs font-medium uppercase tracking-wider text-amber-600 dark:text-amber-400">
                                    Original Base Rule
                                </span>
                                <div className="flex items-center gap-2">
                                    <div className="flex items-center gap-1 rounded bg-amber-500/10 px-2 py-0.5 text-xs text-amber-700 dark:text-amber-300">
                                        <FileText className="h-3 w-3" />
                                        <span>Page {page}</span>
                                    </div>
                                    {confidence && confidence > 0 && (
                                        <div className="rounded bg-amber-500/10 px-2 py-0.5 text-xs text-amber-700 dark:text-amber-300">
                                            {confidence}% match
                                        </div>
                                    )}
                                </div>
                            </div>
                            <blockquote
                                className={cn(
                                    "border-l-3 border-amber-500/40 pl-4 text-sm leading-relaxed",
                                    "text-muted-foreground line-through decoration-amber-500/30"
                                )}
                                style={{
                                    fontFamily: "Georgia, 'Times New Roman', Times, serif",
                                    fontStyle: "italic",
                                }}
                            >
                                &quot;{quote}&quot;
                            </blockquote>
                        </div>

                        {/* Reason for Supersession */}
                        <div className="rounded-md bg-amber-500/10 p-3">
                            <div className="mb-1 flex items-center gap-2 text-xs font-medium text-amber-700 dark:text-amber-300">
                                <AlertOctagon className="h-3 w-3" />
                                Why this changed
                            </div>
                            <p className="text-sm text-amber-800 dark:text-amber-200">
                                {reason}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SupersededCard;

