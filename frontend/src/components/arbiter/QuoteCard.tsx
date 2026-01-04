"use client";

import { AlertTriangle, FileText, CheckCircle, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuoteCardProps {
    quote: string;
    page: number;
    verified: boolean;
    sourceId?: number | null;
    className?: string;
}

export function QuoteCard({ quote, page, verified, sourceId, className }: QuoteCardProps) {
    const handleViewOriginal = () => {
        if (sourceId) {
            window.open(`/source/${sourceId}?page=${page}`, '_blank');
        }
    };

    return (
        <div
            className={cn(
                "rounded-xl border overflow-hidden transition-all duration-300",
                // Darker background than verdict (visual hierarchy)
                verified
                    ? "border-border bg-[#141414]"
                    : "border-amber-500/30 bg-amber-500/5",
                className
            )}
        >
            {/* Warning Banner for Unverified Quotes */}
            {!verified && (
                <div className="flex items-center gap-2 bg-amber-500/10 px-4 py-2 text-sm text-amber-400 border-b border-amber-500/20">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span className="font-medium">Quote could not be verified</span>
                </div>
            )}

            {/* Quote Content */}
            <div className="p-4 sm:p-5">
                {/* Simplified Header - single line with page + view option */}
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <FileText className="h-4 w-4" />
                        <span>Rulebook, Page {page}</span>
                    </div>

                    {/* View Original - inline in header to save space */}
                    {sourceId && (
                        <button
                            onClick={handleViewOriginal}
                            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                            <span>View</span>
                            <ExternalLink className="h-3 w-3" />
                        </button>
                    )}
                </div>

                {/* Quote Text - clean blockquote style */}
                <blockquote className="pl-3 border-l-2 border-emerald-500/40">
                    <p className="text-base leading-relaxed text-foreground/85">
                        "{quote}"
                    </p>
                </blockquote>

                {/* Verified indicator - small and subtle */}
                {verified && (
                    <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-400">
                        <CheckCircle className="h-3.5 w-3.5" />
                        <span>Verified</span>
                    </div>
                )}
            </div>
        </div>
    );
}
