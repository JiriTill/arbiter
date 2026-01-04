"use client";

import { ArrowLeft, Gamepad2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { type HistoryEntry, formatRelativeTime } from "@/lib/mock-history";
import { VerdictCard } from "./VerdictCard";
import { QuoteCard } from "./QuoteCard";
import { SupersededCard } from "./SupersededCard";

interface HistoryDetailProps {
    entry: HistoryEntry;
    onBack: () => void;
    className?: string;
}

export function HistoryDetail({ entry, onBack, className }: HistoryDetailProps) {
    return (
        <div className={cn("animate-in slide-in-from-right-4 duration-200", className)}>
            {/* Header with Back Button */}
            <div className="mb-6 flex items-center gap-3">
                <button
                    type="button"
                    onClick={onBack}
                    className={cn(
                        "flex h-10 w-10 items-center justify-center rounded-lg border border-border",
                        "transition-colors hover:bg-muted active:bg-muted/80"
                    )}
                >
                    <ArrowLeft className="h-5 w-5" />
                </button>
                <div className="flex-1">
                    <h2 className="text-lg font-semibold">Answer Details</h2>
                    <p className="text-xs text-muted-foreground">
                        {formatRelativeTime(entry.timestamp)}
                    </p>
                </div>
            </div>

            {/* Question Context */}
            <div className="mb-4 rounded-lg border border-dashed border-border bg-card/30 p-4">
                <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                        <Gamepad2 className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1">
                        <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="font-medium text-foreground/80">{entry.gameName}</span>
                            <span>•</span>
                            <span>{entry.gameEdition}</span>
                        </div>
                        <p className="font-medium leading-snug">{entry.question}</p>
                    </div>
                </div>
            </div>

            {/* Answer Stack */}
            <div className="space-y-4">
                {/* Verdict */}
                <VerdictCard
                    verdict={entry.verdict}
                    confidence={entry.confidence}
                />

                {/* Quote */}
                <QuoteCard
                    quote={entry.quote}
                    page={entry.quotePage}
                    verified={entry.quoteVerified}
                    edition={entry.sourceEdition} // Pass edition if supported
                />

                {/* Superseded (if exists) */}
                {entry.superseded && (
                    <SupersededCard
                        supersededRule={{
                            quote: entry.superseded.oldQuote,
                            page: entry.superseded.oldPage,
                            reason: entry.superseded.reason,
                            source_type: "rulebook", // Default for mock data
                        }}
                    />
                )}
            </div>
        </div>
    );
}
