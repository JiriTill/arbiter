"use client";

import { useEffect, useState } from "react";
import { Loader2, CheckCircle, BookOpen, FileText, Brain, Database, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { connectToIngestionProgress, getStageLabel, IngestionProgress } from "@/lib/sse";

interface LoadingRitualProps {
    jobId: string;
    gameName: string;
    onComplete?: () => void;
    onError?: (error: string) => void;
    className?: string;
}

// Stage icons and colors
const stageConfig: Record<string, { icon: React.ElementType; color: string }> = {
    queued: { icon: Loader2, color: "text-muted-foreground" },
    downloading: { icon: BookOpen, color: "text-blue-400" },
    extracting: { icon: FileText, color: "text-purple-400" },
    chunking: { icon: Database, color: "text-orange-400" },
    embedding: { icon: Brain, color: "text-pink-400" },
    saving: { icon: Database, color: "text-green-400" },
    ready: { icon: CheckCircle, color: "text-[#4ade80]" },
    failed: { icon: Loader2, color: "text-destructive" },
};

export function LoadingRitual({
    jobId,
    gameName,
    onComplete,
    onError,
    className,
}: LoadingRitualProps) {
    const [progress, setProgress] = useState<IngestionProgress>({
        state: "queued",
        pct: 0,
        msg: "Preparing...",
    });
    const [isConnected, setIsConnected] = useState(true);

    useEffect(() => {
        const cleanup = connectToIngestionProgress(jobId, {
            onProgress: (data) => {
                setProgress(data);
                setIsConnected(true);
            },
            onComplete: (data) => {
                setProgress(data);
                onComplete?.();
            },
            onError: (data) => {
                setProgress(data);
                onError?.(data.error || "Indexing failed");
            },
            onDisconnect: () => {
                setIsConnected(false);
            },
            onReconnect: () => {
                setIsConnected(true);
            },
        });

        return cleanup;
    }, [jobId, onComplete, onError]);

    const config = stageConfig[progress.state] || stageConfig.queued;
    const Icon = config.icon;
    const isComplete = progress.state === "ready";
    const isFailed = progress.state === "failed" || progress.state === "error";

    return (
        <div
            className={cn(
                "rounded-xl border border-border bg-gradient-to-b from-card to-card/80 p-6",
                "animate-in fade-in slide-in-from-bottom-4 duration-500",
                className
            )}
        >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
                <div className={cn(
                    "flex h-12 w-12 items-center justify-center rounded-full",
                    "bg-gradient-to-br from-primary/20 to-primary/5",
                    isComplete && "from-[#4ade80]/20 to-[#4ade80]/5"
                )}>
                    <Icon className={cn(
                        "h-6 w-6 transition-colors duration-300",
                        config.color,
                        !isComplete && !isFailed && "animate-spin"
                    )} />
                </div>
                <div>
                    <h3 className="font-semibold text-lg">
                        {isComplete ? "Ready!" : isFailed ? "Indexing Failed" : "Indexing Rules"}
                    </h3>
                    <p className="text-sm text-muted-foreground">{gameName}</p>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-3 mb-6">
                <div className="relative h-3 rounded-full bg-muted overflow-hidden">
                    <div
                        className={cn(
                            "absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out",
                            isComplete ? "bg-[#4ade80]" : isFailed ? "bg-destructive" : "bg-primary",
                        )}
                        style={{ width: `${progress.pct}%` }}
                    >
                        {/* Shimmer effect */}
                        {!isComplete && !isFailed && (
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                        )}
                    </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                    <span className={cn("font-medium", config.color)}>
                        {getStageLabel(progress.state)}
                    </span>
                    <span className="text-muted-foreground tabular-nums">
                        {progress.pct}%
                    </span>
                </div>
            </div>

            {/* Status Message */}
            <div className={cn(
                "rounded-lg border border-border bg-muted/30 p-4",
                "transition-all duration-300"
            )}>
                <p className="text-sm text-muted-foreground leading-relaxed">
                    {progress.msg || "Processing your request..."}
                </p>

                {!isConnected && (
                    <p className="text-xs text-amber-500 mt-2 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Reconnecting...
                    </p>
                )}
            </div>

            {/* Completion State */}
            {isComplete && (
                <div className="mt-6 flex items-center gap-2 text-[#4ade80]">
                    <Sparkles className="h-4 w-4" />
                    <span className="text-sm font-medium">
                        Rules indexed! You can now ask questions.
                    </span>
                </div>
            )}

            {/* Error State */}
            {isFailed && progress.error && (
                <div className="mt-6 text-sm text-destructive">
                    {progress.error}
                </div>
            )}
        </div>
    );
}
