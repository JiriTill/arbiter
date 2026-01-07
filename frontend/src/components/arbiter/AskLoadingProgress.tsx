"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
    BookOpen,
    Search,
    FileCheck,
    Sparkles,
    Check,
    Loader2
} from "lucide-react";

interface LoadingStep {
    id: string;
    label: string;
    icon: React.ElementType;
    duration: number; // milliseconds to show this step
}

const LOADING_STEPS: LoadingStep[] = [
    { id: "search", label: "Searching rulebook...", icon: BookOpen, duration: 1500 },
    { id: "analyze", label: "Analyzing relevant passages...", icon: Search, duration: 2000 },
    { id: "verify", label: "Verifying citations...", icon: FileCheck, duration: 2000 },
    { id: "compose", label: "Composing verdict...", icon: Sparkles, duration: 1500 },
];

interface AskLoadingProgressProps {
    className?: string;
    gameName?: string;
}

export function AskLoadingProgress({ className, gameName }: AskLoadingProgressProps) {
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [elapsedTime, setElapsedTime] = useState(0);

    // Progress through steps
    useEffect(() => {
        let stepTimer: NodeJS.Timeout;
        let elapsed = 0;

        const advanceStep = () => {
            if (currentStepIndex < LOADING_STEPS.length - 1) {
                elapsed += LOADING_STEPS[currentStepIndex].duration;
                setCurrentStepIndex(prev => prev + 1);
                stepTimer = setTimeout(advanceStep, LOADING_STEPS[currentStepIndex + 1].duration);
            }
        };

        stepTimer = setTimeout(advanceStep, LOADING_STEPS[0].duration);

        return () => clearTimeout(stepTimer);
    }, []);

    // Elapsed time counter
    useEffect(() => {
        const interval = setInterval(() => {
            setElapsedTime(prev => prev + 100);
        }, 100);

        return () => clearInterval(interval);
    }, []);

    const currentStep = LOADING_STEPS[currentStepIndex];
    const progressPercent = ((currentStepIndex + 1) / LOADING_STEPS.length) * 100;

    return (
        <div className={cn("space-y-6 p-6 rounded-xl border border-border bg-card", className)}>
            {/* Header */}
            <div className="text-center space-y-2">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-500 text-sm font-medium">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Consulting The Arbiter
                </div>
                {gameName && (
                    <p className="text-xs text-muted-foreground">
                        Searching {gameName} rulebook
                    </p>
                )}
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${progressPercent}%` }}
                    />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{(elapsedTime / 1000).toFixed(1)}s</span>
                    <span>{Math.round(progressPercent)}%</span>
                </div>
            </div>

            {/* Steps */}
            <div className="space-y-3">
                {LOADING_STEPS.map((step, index) => {
                    const Icon = step.icon;
                    const isActive = index === currentStepIndex;
                    const isComplete = index < currentStepIndex;
                    const isPending = index > currentStepIndex;

                    return (
                        <div
                            key={step.id}
                            className={cn(
                                "flex items-center gap-3 p-3 rounded-lg transition-all duration-300",
                                isActive && "bg-emerald-500/10 border border-emerald-500/30",
                                isComplete && "opacity-60",
                                isPending && "opacity-30"
                            )}
                        >
                            {/* Icon */}
                            <div className={cn(
                                "h-8 w-8 rounded-full flex items-center justify-center transition-colors",
                                isActive && "bg-emerald-500 text-white",
                                isComplete && "bg-muted text-emerald-500",
                                isPending && "bg-muted text-muted-foreground"
                            )}>
                                {isComplete ? (
                                    <Check className="h-4 w-4" />
                                ) : isActive ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Icon className="h-4 w-4" />
                                )}
                            </div>

                            {/* Label */}
                            <span className={cn(
                                "text-sm font-medium transition-colors",
                                isActive && "text-foreground",
                                isComplete && "text-muted-foreground",
                                isPending && "text-muted-foreground"
                            )}>
                                {step.label}
                            </span>

                            {/* Active indicator */}
                            {isActive && (
                                <div className="ml-auto">
                                    <div className="flex gap-1">
                                        <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                        <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                        <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Footer tip */}
            <p className="text-xs text-center text-muted-foreground">
                First-time queries may take a few extra seconds
            </p>
        </div>
    );
}
