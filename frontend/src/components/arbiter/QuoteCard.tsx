"use client";

import { Quote, AlertTriangle, FileText, CheckCircle, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuoteCardProps {
    quote: string;
    page: number;
    verified: boolean;
    className?: string;
}

export function QuoteCard({ quote, page, verified, className }: QuoteCardProps) {
    return (
        <div
            className={cn(
                "rounded-2xl border-2 overflow-hidden transition-all duration-300",
                verified
                    ? "border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-transparent"
                    : "border-amber-500/30 bg-amber-500/5",
                className
            )}
        >
            {/* Warning Banner for Unverified Quotes */}
            {!verified && (
                <div className="flex items-center gap-2 bg-amber-500/10 px-4 py-2 text-sm text-amber-400 border-b border-amber-500/20">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span className="font-medium">Quote could not be verified against source</span>
                </div>
            )}

            {/* Quote Content */}
            <div className="p-6">
                {/* Header */}
                <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center">
                            <BookOpen className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                            From the Rulebook
                        </span>
                    </div>

                    {/* Page Badge */}
                    <div className="flex items-center gap-1.5 rounded-full bg-muted px-3 py-1.5 text-xs font-medium">
                        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>Page {page}</span>
                    </div>
                </div>

                {/* Quote Text - Styled blockquote */}
                <blockquote className="relative pl-4 border-l-3 border-emerald-500/50">
                    <Quote className="absolute -left-2 -top-1 h-5 w-5 text-emerald-500/30" />
                    <p
                        className="text-lg leading-relaxed text-foreground/90"
                        style={{
                            fontFamily: "Georgia, 'Times New Roman', Times, serif",
                            fontStyle: "italic",
                        }}
                    >
                        &ldquo;{quote}&rdquo;
                    </p>
                </blockquote>

                {/* Verified indicator */}
                {verified && (
                    <div className="mt-4 flex items-center gap-2 text-sm text-emerald-400">
                        <div className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20">
                            <CheckCircle className="h-3.5 w-3.5" />
                        </div>
                        <span className="font-medium">Verified against source</span>
                    </div>
                )}
            </div>
        </div>
    );
}
