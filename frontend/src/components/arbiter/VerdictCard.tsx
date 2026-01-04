"use client";

import { useState } from "react";
import { CheckCircle, AlertTriangle, HelpCircle, Share2, Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

type Confidence = "high" | "medium" | "low";

interface VerdictCardProps {
    verdict: string;
    confidence: Confidence;
    gameName?: string;
    question?: string;
    className?: string;
}

const confidenceConfig: Record<
    Confidence,
    {
        icon: React.ElementType;
        label: string;
        color: string;
        bgColor: string;
        borderColor: string;
        glowColor: string;
        description: string;
    }
> = {
    high: {
        icon: CheckCircle,
        label: "High confidence",
        color: "text-emerald-400",
        bgColor: "bg-emerald-500/10",
        borderColor: "border-emerald-500/30",
        glowColor: "shadow-emerald-500/20",
        description: "This answer is directly supported by the rulebook",
    },
    medium: {
        icon: AlertTriangle,
        label: "Medium confidence",
        color: "text-amber-400",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/30",
        glowColor: "shadow-amber-500/20",
        description: "Answer based on interpretation of the rules",
    },
    low: {
        icon: HelpCircle,
        label: "Low confidence",
        color: "text-red-400",
        bgColor: "bg-red-500/10",
        borderColor: "border-red-500/30",
        glowColor: "shadow-red-500/20",
        description: "Limited information found in the rulebook",
    },
};

// Gavel SVG component with animation
function GavelIcon({ className }: { className?: string }) {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("animate-gavel", className)}
        >
            {/* Handle */}
            <path d="M14.5 12.5L6 21l-3-3 8.5-8.5" />
            {/* Head connection */}
            <path d="M18.5 8.5L21 6l-3-3-2.5 2.5" />
            {/* Striking motion line */}
            <path d="M12 10l4-4" />
            {/* Gavel head */}
            <rect x="14" y="4" width="6" height="4" rx="1" transform="rotate(45 17 6)" />
        </svg>
    );
}

export function VerdictCard({ verdict, confidence, gameName, question, className }: VerdictCardProps) {
    const [copied, setCopied] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);
    const config = confidenceConfig[confidence];
    const Icon = config.icon;

    // Detect if verdict starts with YES or NO for special styling
    const verdictLower = verdict.toLowerCase().trim();
    const startsWithYes = verdictLower.startsWith("yes");
    const startsWithNo = verdictLower.startsWith("no");

    // Split verdict for highlighting YES/NO
    let highlightWord = "";
    let restOfVerdict = verdict;

    if (startsWithYes) {
        highlightWord = verdict.slice(0, 3);
        restOfVerdict = verdict.slice(3);
    } else if (startsWithNo) {
        highlightWord = verdict.slice(0, 2);
        restOfVerdict = verdict.slice(2);
    }

    const handleShare = async () => {
        const shareText = `🎲 The Arbiter's Verdict${gameName ? ` for ${gameName}` : ""}:\n\n${question ? `Q: ${question}\n\n` : ""}A: ${verdict}`;

        if (navigator.share) {
            try {
                await navigator.share({
                    title: "The Arbiter's Verdict",
                    text: shareText,
                });
            } catch {
                // User cancelled or share failed, fallback to copy
                copyToClipboard(shareText);
            }
        } else {
            copyToClipboard(shareText);
        }
    };

    const copyToClipboard = async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            console.error("Failed to copy");
        }
    };

    return (
        <div
            className={cn(
                "relative rounded-2xl border-2 p-6 transition-all duration-300",
                config.borderColor,
                config.bgColor,
                "shadow-lg",
                config.glowColor,
                className
            )}
        >
            {/* Top bar with gavel and confidence */}
            <div className="flex items-start justify-between mb-4">
                {/* Gavel icon with animation */}
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center",
                        "bg-gradient-to-br from-emerald-500/20 to-emerald-600/10",
                        "border border-emerald-500/30"
                    )}>
                        <GavelIcon className="h-6 w-6 text-emerald-400" />
                    </div>
                    <div>
                        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                            The Verdict
                        </span>
                    </div>
                </div>

                {/* Confidence Badge with tooltip */}
                <div
                    className="relative"
                    onMouseEnter={() => setShowTooltip(true)}
                    onMouseLeave={() => setShowTooltip(false)}
                >
                    <div
                        className={cn(
                            "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium cursor-help",
                            config.bgColor,
                            config.color,
                            "border",
                            config.borderColor
                        )}
                    >
                        <Icon className="h-3.5 w-3.5" />
                        <span>{config.label}</span>
                    </div>

                    {/* Tooltip */}
                    {showTooltip && (
                        <div className="absolute z-10 right-0 top-full mt-2 w-48 p-2 rounded-lg bg-popover border border-border shadow-xl text-xs text-muted-foreground animate-in fade-in slide-in-from-top-1 duration-200">
                            {config.description}
                        </div>
                    )}
                </div>
            </div>

            {/* Verdict Text - with YES/NO highlighting */}
            <div className="text-xl font-semibold leading-relaxed text-foreground sm:text-2xl">
                {highlightWord ? (
                    <>
                        <span className={cn(
                            "inline-block mr-1.5 px-2 py-0.5 rounded-md font-bold",
                            startsWithYes ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                        )}>
                            {highlightWord.toUpperCase()}
                        </span>
                        <span>{restOfVerdict}</span>
                    </>
                ) : (
                    <span>{verdict}</span>
                )}
            </div>

            {/* Share button */}
            <div className="mt-4 pt-4 border-t border-border/50 flex justify-end">
                <button
                    onClick={handleShare}
                    className={cn(
                        "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm",
                        "text-muted-foreground hover:text-foreground",
                        "hover:bg-muted/50 transition-colors"
                    )}
                >
                    {copied ? (
                        <>
                            <Check className="h-4 w-4 text-emerald-400" />
                            <span className="text-emerald-400">Copied!</span>
                        </>
                    ) : (
                        <>
                            <Share2 className="h-4 w-4" />
                            <span>Share verdict</span>
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}
