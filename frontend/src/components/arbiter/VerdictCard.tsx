"use client";

import { CheckCircle, AlertTriangle, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

type Confidence = "high" | "medium" | "low";

interface VerdictCardProps {
    verdict: string;
    confidence: Confidence;
    className?: string;
}

const confidenceConfig: Record<
    Confidence,
    { icon: React.ElementType; label: string; color: string; bgColor: string }
> = {
    high: {
        icon: CheckCircle,
        label: "High confidence",
        color: "text-[#4ade80]",
        bgColor: "bg-[#4ade80]/10",
    },
    medium: {
        icon: AlertTriangle,
        label: "Medium confidence",
        color: "text-[#fbbf24]",
        bgColor: "bg-[#fbbf24]/10",
    },
    low: {
        icon: HelpCircle,
        label: "Low confidence",
        color: "text-[#f87171]",
        bgColor: "bg-[#f87171]/10",
    },
};

export function VerdictCard({ verdict, confidence, className }: VerdictCardProps) {
    const config = confidenceConfig[confidence];
    const Icon = config.icon;

    return (
        <div
            className={cn(
                "relative rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-6",
                className
            )}
        >
            {/* Confidence Badge */}
            <div
                className={cn(
                    "absolute right-4 top-4 flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
                    config.bgColor,
                    config.color
                )}
            >
                <Icon className="h-3.5 w-3.5" />
                <span>{config.label}</span>
            </div>

            {/* Verdict Label */}
            <div className="mb-2">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Verdict
                </span>
            </div>

            {/* Verdict Text */}
            <p className="pr-32 text-xl font-semibold leading-relaxed text-foreground sm:text-2xl">
                {verdict}
            </p>
        </div>
    );
}
