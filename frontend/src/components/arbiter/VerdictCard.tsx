"use client";

import { useState } from "react";
import { CheckCircle, AlertTriangle, HelpCircle, Share2, Copy, Check, Info } from "lucide-react";
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
        sublabel: string;
        color: string;
        bgColor: string;
        borderColor: string;
        cardBg: string;
        showBoldVerdict: boolean;
    }
> = {
    high: {
        icon: CheckCircle,
        label: "High confidence",
        sublabel: "Directly answered by the rulebook",
        color: "text-emerald-400",
        bgColor: "bg-emerald-500/10",
        borderColor: "border-emerald-500/30",
        cardBg: "bg-[#1a2a1f]",
        showBoldVerdict: true,
    },
    medium: {
        icon: AlertTriangle,
        label: "Medium confidence",
        sublabel: "Based on rule interpretation",
        color: "text-amber-400",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/30",
        cardBg: "bg-[#2a2516]",
        showBoldVerdict: true,
    },
    low: {
        icon: Info,
        label: "Possible answer",
        sublabel: "Verified quote, but may not fully cover your scenario",
        color: "text-amber-400",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/30",
        cardBg: "bg-[#252520]",
        showBoldVerdict: false, // Don't show bold YES/NO for low confidence
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
            <path d="M14.5 12.5L6 21l-3-3 8.5-8.5" />
            <path d="M18.5 8.5L21 6l-3-3-2.5 2.5" />
            <path d="M12 10l4-4" />
            <rect x="14" y="4" width="6" height="4" rx="1" transform="rotate(45 17 6)" />
        </svg>
    );
}

export function VerdictCard({ verdict, confidence, gameName, question, className }: VerdictCardProps) {
    const [copied, setCopied] = useState(false);
    const config = confidenceConfig[confidence];
    const Icon = config.icon;

    // Detect if verdict starts with YES or NO for special styling
    const verdictLower = verdict.toLowerCase().trim();
    const startsWithYes = verdictLower.startsWith("yes");
    const startsWithNo = verdictLower.startsWith("no");

    // Split verdict for highlighting YES/NO (only for high/medium confidence)
    let highlightWord = "";
    let restOfVerdict = verdict;

    if (config.showBoldVerdict) {
        if (startsWithYes) {
            highlightWord = verdict.slice(0, 3);
            restOfVerdict = verdict.slice(3);
        } else if (startsWithNo) {
            highlightWord = verdict.slice(0, 2);
            restOfVerdict = verdict.slice(2);
        }
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
                "relative rounded-2xl border-2 overflow-hidden transition-all duration-300",
                config.borderColor,
                config.cardBg,
                className
            )}
        >
            {/* Low confidence warning banner */}
            {confidence === "low" && (
                <div className="flex items-center gap-2 px-4 py-2.5 bg-amber-500/10 border-b border-amber-500/20">
                    <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                    <span className="text-sm text-amber-300">
                        This answer may not fully address your specific situation
                    </span>
                </div>
            )}

            <div className="p-6">
                {/* Top bar with gavel and confidence */}
                <div className="flex items-start justify-between mb-4">
                    {/* Gavel icon with animation */}
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            "w-12 h-12 rounded-xl flex items-center justify-center",
                            confidence === "high"
                                ? "bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30"
                                : "bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30"
                        )}>
                            <GavelIcon className={cn(
                                "h-6 w-6",
                                confidence === "high" ? "text-emerald-400" : "text-amber-400"
                            )} />
                        </div>
                        <div>
                            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                                The Verdict
                            </span>
                        </div>
                    </div>

                    {/* Confidence Badge */}
                    <div className="relative group">
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
                        <div className="absolute z-10 right-0 top-full mt-2 w-56 p-3 rounded-lg bg-popover border border-border shadow-xl text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                            <p className="font-medium text-foreground mb-1">{config.label}</p>
                            <p>{config.sublabel}</p>
                        </div>
                    </div>
                </div>

                {/* Verdict Text */}
                <div className={cn(
                    "text-xl leading-relaxed sm:text-2xl",
                    confidence === "low" ? "text-foreground/80" : "text-foreground font-semibold"
                )}>
                    {highlightWord && config.showBoldVerdict ? (
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
        </div>
    );
}
