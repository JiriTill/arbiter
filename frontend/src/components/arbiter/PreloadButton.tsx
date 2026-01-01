"use client";

import { useState, useCallback } from "react";
import { Loader2, Download, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

interface PreloadButtonProps {
    gameId: number;
    gameName: string;
    edition?: string;
    isIndexed?: boolean;
    onIndexingStart?: (jobId: string) => void;
    onIndexingComplete?: () => void;
    className?: string;
}

type PreloadState = "idle" | "loading" | "indexing" | "complete" | "error";

export function PreloadButton({
    gameId,
    gameName,
    edition,
    isIndexed = false,
    onIndexingStart,
    onIndexingComplete,
    className,
}: PreloadButtonProps) {
    const [state, setState] = useState<PreloadState>(isIndexed ? "complete" : "idle");
    const [error, setError] = useState<string | null>(null);

    const handlePreload = useCallback(async () => {
        if (state === "loading" || state === "indexing" || state === "complete") return;

        setState("loading");
        setError(null);

        try {
            // Call the ingest endpoint
            const response = await api.post<{
                job_id: string;
                source_id: number;
                status_url: string;
                events_url: string;
                estimated_seconds: number;
            }>("/ingest", {
                source_id: gameId,
                force: false,
            });

            setState("indexing");
            onIndexingStart?.(response.job_id);
        } catch (err) {
            console.error("Failed to start indexing:", err);
            setState("error");
            setError(err instanceof Error ? err.message : "Failed to start indexing");
        }
    }, [gameId, state, onIndexingStart]);

    // Update state when indexing completes externally
    const markComplete = useCallback(() => {
        setState("complete");
        onIndexingComplete?.();
    }, [onIndexingComplete]);

    // Render based on state
    if (state === "complete" || isIndexed) {
        return (
            <div className={cn(
                "flex items-center gap-2 text-[#4ade80] text-sm",
                className
            )}>
                <CheckCircle className="h-4 w-4" />
                <span>Rules indexed</span>
            </div>
        );
    }

    if (state === "error") {
        return (
            <div className={cn("space-y-2", className)}>
                <div className="flex items-center gap-2 text-destructive text-sm">
                    <AlertCircle className="h-4 w-4" />
                    <span>{error || "Failed to preload"}</span>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                        setState("idle");
                        setError(null);
                    }}
                >
                    Try Again
                </Button>
            </div>
        );
    }

    if (state === "loading" || state === "indexing") {
        return (
            <Button
                variant="outline"
                size="sm"
                disabled
                className={cn("opacity-70", className)}
            >
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {state === "loading" ? "Starting..." : "Indexing..."}
            </Button>
        );
    }

    // Idle state
    return (
        <Button
            variant="outline"
            size="sm"
            onClick={handlePreload}
            className={cn(
                "text-muted-foreground hover:text-foreground",
                className
            )}
        >
            <Download className="mr-2 h-4 w-4" />
            Preload Rules
        </Button>
    );
}
