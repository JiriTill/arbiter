"use client";

import { useState, useEffect } from "react";
import { VerdictCard } from "@/components/arbiter/VerdictCard";
import { cn } from "@/lib/utils";
import type { Confidence } from "@/types/arbiter";

interface ShowcaseExample {
    id: number;
    gameName: string;
    question: string;
    verdict: string;
    confidence: Confidence;
}

const EXAMPLES: ShowcaseExample[] = [
    {
        id: 1,
        gameName: "Catan",
        question: "Can I play a Knight card before I roll the dice?",
        verdict: "Yes, you can play a Development Card (including a Knight) before rolling the dice. However, you cannot play a card you bought typically on the same turn.",
        confidence: "high"
    },
    {
        id: 2,
        gameName: "Wingspan",
        question: "Do eggs stay on birds if I trade them for food?",
        verdict: "No, typically you discard eggs to pay for costs. If a bird power allows trading eggs for food, the eggs are removed from the bird card and returned to the supply.",
        confidence: "medium"
    },
    {
        id: 3,
        gameName: "Ticket to Ride",
        question: "Can I claim two routes between same cities in 2 player game?",
        verdict: "No, in 2 or 3 player games, only ONE of the double routes can be claimed. The other is closed immediately.",
        confidence: "high"
    }
];

export function VerdictShowcase() {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPaused, setIsPaused] = useState(false);

    useEffect(() => {
        if (isPaused) return;

        const interval = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % EXAMPLES.length);
        }, 5000);

        return () => clearInterval(interval);
    }, [isPaused]);

    return (
        <div
            className="relative w-full max-w-2xl mx-auto perspective-1000"
            onMouseEnter={() => setIsPaused(true)}
            onMouseLeave={() => setIsPaused(false)}
        >
            {/* Background blur effect */}
            <div className="absolute inset-0 bg-emerald-500/5 blur-3xl -z-10 rounded-full dark:bg-emerald-500/10" />

            {/* Cards Stack */}
            <div className="relative min-h-[300px]">
                {EXAMPLES.map((example, idx) => {
                    const isCurrent = idx === currentIndex;
                    // Simply stack them, only current is fully visible
                    // Others hidden or behind? Let's just fade them nicely.
                    // Actually, let's just render one with a nice transition

                    if (!isCurrent) return null;

                    return (
                        <div
                            key={example.id}
                            className="animate-in fade-in slide-in-from-bottom-4 duration-500"
                        >
                            <VerdictCard
                                verdict={example.verdict}
                                confidence={example.confidence}
                                gameName={example.gameName}
                                question={example.question}
                                className="shadow-2xl shadow-black/20"
                            />
                        </div>
                    );
                })}
            </div>

            {/* Indicators */}
            <div className="flex justify-center gap-2 mt-6">
                {EXAMPLES.map((_, idx) => (
                    <button
                        key={idx}
                        onClick={() => setCurrentIndex(idx)}
                        className={cn(
                            "w-2 h-2 rounded-full transition-all duration-300",
                            currentIndex === idx
                                ? "w-6 bg-emerald-500"
                                : "bg-muted-foreground/30 hover:bg-emerald-500/50"
                        )}
                        aria-label={`Go to example ${idx + 1}`}
                    />
                ))}
            </div>
        </div>
    );
}
