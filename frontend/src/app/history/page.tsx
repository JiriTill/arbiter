"use client";

import { useState } from "react";
import { HistoryList, HistoryDetail } from "@/components/arbiter";
import { MOCK_HISTORY, type HistoryEntry } from "@/lib/mock-history";

export default function HistoryPage() {
    const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);

    // For demo, use mock data - in production this would come from context/API
    const historyEntries = MOCK_HISTORY;

    return (
        <div className="min-h-[calc(100vh-5rem)] p-4 sm:p-6">
            {/* Conditional rendering with smooth transitions */}
            {selectedEntry ? (
                // Detail View
                <HistoryDetail
                    entry={selectedEntry}
                    onBack={() => setSelectedEntry(null)}
                />
            ) : (
                // List View
                <div className="animate-in fade-in duration-150">
                    {/* Header */}
                    <div className="mb-6">
                        <h1 className="text-2xl font-bold tracking-tight">History</h1>
                        <p className="mt-1 text-muted-foreground">
                            Your previous questions and answers
                        </p>
                    </div>

                    {/* Filter/Sort options - placeholder for future */}
                    {historyEntries.length > 0 && (
                        <div className="mb-4 flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">
                                {historyEntries.length} question{historyEntries.length !== 1 ? "s" : ""}
                            </span>
                            {/* Future: Add filter/sort buttons here */}
                        </div>
                    )}

                    {/* History List */}
                    <HistoryList
                        entries={historyEntries}
                        onSelectEntry={setSelectedEntry}
                    />
                </div>
            )}

            {/* Bottom padding for nav */}
            <div className="h-8" />
        </div>
    );
}
