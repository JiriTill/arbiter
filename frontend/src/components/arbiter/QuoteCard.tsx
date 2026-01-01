"use client";

import { Quote, AlertTriangle, FileText } from "lucide-react";
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
                "rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] overflow-hidden",
                className
            )}
        >
            {/* Warning Banner for Unverified Quotes */}
            {!verified && (
                <div className="flex items-center gap-2 bg-[#f87171]/10 px-4 py-2 text-sm text-[#f87171]">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span className="font-medium">Quote not verified against source document</span>
                </div>
            )}

            {/* Quote Content */}
            <div className="p-6">
                {/* Header */}
                <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Quote className="h-4 w-4 text-muted-foreground" />
                        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                            From the Rulebook
                        </span>
                    </div>

                    {/* Page Badge */}
                    <div className="flex items-center gap-1.5 rounded-md bg-muted px-2.5 py-1 text-xs font-medium">
                        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>Page {page}</span>
                    </div>
                </div>

                {/* Quote Text - Georgia Serif Italic */}
                <blockquote
                    className="border-l-2 border-primary/50 pl-4 text-lg leading-relaxed"
                    style={{
                        fontFamily: "Georgia, 'Times New Roman', Times, serif",
                        fontStyle: "italic",
                    }}
                >
                    "{quote}"
                </blockquote>

                {/* Verified indicator */}
                {verified && (
                    <div className="mt-4 flex items-center gap-1.5 text-xs text-[#4ade80]">
                        <svg
                            className="h-3.5 w-3.5"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                        >
                            <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                            />
                        </svg>
                        <span>Verified against source</span>
                    </div>
                )}
            </div>
        </div>
    );
}
