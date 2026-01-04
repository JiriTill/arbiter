"use client";

import { useState } from "react";
import { Gamepad2, Clock, ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface RecentQuestion {
    id: string;
    question: string;
    gameName: string;
    timestamp: string;
}

interface RecentQuestionsProps {
    questions: RecentQuestion[];
    onQuestionClick?: (question: RecentQuestion) => void;
    className?: string;
}

// Placeholder recent questions for UI development
const PLACEHOLDER_QUESTIONS: RecentQuestion[] = [
    {
        id: "1",
        question: "Can I trade with the bank if I have a 2:1 port for that resource?",
        gameName: "Catan",
        timestamp: "Just now",
    },
    {
        id: "2",
        question: "Does the robber block resource production for all players or just the one who rolled?",
        gameName: "Catan",
        timestamp: "5 min ago",
    },
    {
        id: "3",
        question: "Can I claim multiple routes between the same two cities?",
        gameName: "Ticket to Ride",
        timestamp: "1 hour ago",
    },
    {
        id: "4",
        question: "When do I score bonus points for eggs in the same row?",
        gameName: "Wingspan",
        timestamp: "Earlier today",
    },
    {
        id: "5",
        question: "Can I use a rest action if I have no cards to recover?",
        gameName: "Gloomhaven",
        timestamp: "Yesterday",
    },
];

function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + "...";
}

export function RecentQuestions({
    questions,
    onQuestionClick,
    className
}: RecentQuestionsProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    // Use placeholder data if no questions provided or if the provided array is empty
    const displayQuestions = questions && questions.length > 0 ? questions : PLACEHOLDER_QUESTIONS;

    if (displayQuestions.length === 0) {
        return null;
    }

    const visibleQuestions = isExpanded ? displayQuestions : displayQuestions.slice(0, 3);
    const hasMore = displayQuestions.length > 3;

    return (
        <div className={cn("space-y-4", className)}>
            <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    Recent Questions
                </h2>
            </div>

            <div className="space-y-2">
                {visibleQuestions.map((item) => (
                    <button
                        key={item.id}
                        type="button"
                        onClick={() => onQuestionClick?.(item)}
                        className={cn(
                            "flex w-full items-start gap-3 rounded-lg border border-border bg-card p-3 text-left transition-all duration-200",
                            "hover:bg-muted/30 hover:border-emerald-500/30 active:scale-[0.99]",
                        )}
                    >
                        {/* Game Icon */}
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted/50 mt-0.5">
                            <Gamepad2 className="h-4 w-4 text-muted-foreground" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium leading-snug">
                                {truncateText(item.question, 70)}
                            </p>
                            <div className="mt-1.5 flex items-center gap-2 text-xs">
                                <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 font-medium text-emerald-500/80 border border-emerald-500/20">
                                    {item.gameName}
                                </span>
                                <span className="text-muted-foreground">•</span>
                                <span className="text-muted-foreground">{item.timestamp}</span>
                            </div>
                        </div>

                        {/* Arrow */}
                        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/50 mt-1" />
                    </button>
                ))}
            </div>

            {hasMore && (
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full flex items-center justify-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground py-2 transition-colors"
                >
                    {isExpanded ? (
                        <>
                            Show less
                            <ChevronDown className="h-3 w-3 rotate-180 transition-transform" />
                        </>
                    ) : (
                        <>
                            Show more ({displayQuestions.length - 3})
                            <ChevronDown className="h-3 w-3 transition-transform" />
                        </>
                    )}
                </button>
            )}
        </div>
    );
}
