"use client";

import { History, MessageCircleQuestion } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { type HistoryEntry } from "@/lib/mock-history";
import { HistoryItem } from "./HistoryItem";
import { Button } from "@/components/ui/button";

interface HistoryListProps {
    entries: HistoryEntry[];
    onSelectEntry: (entry: HistoryEntry) => void;
    className?: string;
}

export function HistoryList({ entries, onSelectEntry, className }: HistoryListProps) {
    // Empty state
    if (entries.length === 0) {
        return (
            <div className={cn("flex flex-col items-center justify-center py-16 text-center", className)}>
                <div className="mb-4 rounded-full bg-muted p-4">
                    <History className="h-8 w-8 text-muted-foreground" />
                </div>
                <h2 className="text-lg font-medium">No questions yet</h2>
                <p className="mt-2 max-w-xs text-sm text-muted-foreground">
                    Your question history will appear here once you start asking The Arbiter about game rules.
                </p>
                <Link href="/ask" className="mt-6">
                    <Button className="bg-[#4ade80] text-black hover:bg-[#4ade80]/90">
                        <MessageCircleQuestion className="mr-2 h-4 w-4" />
                        Ask your first question
                    </Button>
                </Link>
            </div>
        );
    }

    return (
        <div className={cn("divide-y divide-[#2a2a2a] rounded-lg border border-[#2a2a2a] bg-[#0f0f0f]", className)}>
            {entries.map((entry) => (
                <HistoryItem
                    key={entry.id}
                    entry={entry}
                    onClick={() => onSelectEntry(entry)}
                />
            ))}
        </div>
    );
}
