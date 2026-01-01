"use client";

import { BookOpen, HelpCircle, AlertCircle, ExternalLink, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

type SourceType = "rulebook" | "faq" | "errata";

interface CitationCardProps {
    sourceType: SourceType;
    edition?: string;
    sourceUrl?: string;
    page: number;
    className?: string;
    sourceId?: number | null;
    quote?: string;
}

const sourceConfig: Record<
    SourceType,
    { icon: React.ElementType; label: string; color: string; bgColor: string }
> = {
    rulebook: {
        icon: BookOpen,
        label: "Rulebook",
        color: "text-blue-400",
        bgColor: "bg-blue-400/10",
    },
    faq: {
        icon: HelpCircle,
        label: "FAQ",
        color: "text-purple-400",
        bgColor: "bg-purple-400/10",
    },
    errata: {
        icon: AlertCircle,
        label: "Errata",
        color: "text-orange-400",
        bgColor: "bg-orange-400/10",
    },
};

export function CitationCard({
    sourceType,
    edition,
    sourceUrl,
    page,
    className,
    sourceId,
    quote,
}: CitationCardProps) {
    const config = sourceConfig[sourceType];
    const Icon = config.icon;

    // Determine target URL
    // Prefer internal viewer if sourceId is available
    const viewerUrl = sourceId
        ? `/source/${sourceId}?page=${page}${quote ? `&quote=${encodeURIComponent(quote)}` : ""}`
        : sourceUrl;

    return (
        <div
            className={cn(
                "rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4",
                className
            )}
        >
            <div className="flex items-center justify-between gap-4">
                {/* Left side: Source info */}
                <div className="flex items-center gap-3">
                    {/* Source Type Badge */}
                    <div
                        className={cn(
                            "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium",
                            config.bgColor,
                            config.color
                        )}
                    >
                        <Icon className="h-4 w-4" />
                        <span>{config.label}</span>
                    </div>

                    {/* Edition & Page */}
                    <div className="flex flex-col gap-0.5">
                        {edition && (
                            <span className="text-sm font-medium text-foreground">{edition}</span>
                        )}
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <FileText className="h-3 w-3" />
                            <span>Page {page}</span>
                        </div>
                    </div>
                </div>

                {/* Right side: View Original button */}
                {viewerUrl && (
                    <a
                        href={viewerUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={cn(
                            "flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm font-medium",
                            "text-muted-foreground transition-colors",
                            "hover:bg-muted hover:text-foreground",
                            "active:bg-muted/80"
                        )}
                    >
                        <span>View Original</span>
                        <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                )}
            </div>
        </div>
    );
}
