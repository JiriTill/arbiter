"use client";

import { Gamepad2, Clock, ChevronRight } from "lucide-react";
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
        timestamp: "2 min ago",
    },
    {
        id: "2",
        question: "Does the robber block resource production for all players or just the one who rolled?",
        gameName: "Catan",
        timestamp: "15 min ago",
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
        timestamp: "3 hours ago",
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
    // Use placeholder data if no questions provided or if the provided array is empty
    const displayQuestions = questions && questions.length > 0 ? questions : PLACEHOLDER_QUESTIONS;

    // If after checking, there are still no questions (e.g., PLACEHOLDER_QUESTIONS was also empty, though unlikely here)
    if (displayQuestions.length === 0) {
        return null;
    }

    return (
        <div className={cn("space-y-3", className)}>
            <h2 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Clock className="h-4 w-4" />
                Recent Questions
            </h2>

            <div className="space-y-2">
                {displayQuestions.slice(0, 5).map((item) => (
                    <button
                        key={item.id}
                        type="button"
                        onClick={() => onQuestionClick?.(item)}
                        className={cn(
                            "flex w-full items-start gap-3 rounded-lg border border-border bg-card p-3 text-left transition-colors",
                            "hover:bg-card/80 active:bg-card/70",
                            "min-h-[56px]" // Large tap target
                        )}
                    >
                        {/* Game Icon */}
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted mt-0.5">
                            <Gamepad2 className="h-4 w-4 text-muted-foreground" />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium leading-snug">
                                {truncateText(item.question, 60)}
                            </p>
                            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                                <span className="rounded bg-muted px-1.5 py-0.5">{item.gameName}</span>
                                <span>•</span>
                                <span>{item.timestamp}</span>
                            </div>
                        </div>

                        {/* Arrow */}
                        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground mt-1" />
                    </button>
                ))}
            </div>
        </div>
    );
}
