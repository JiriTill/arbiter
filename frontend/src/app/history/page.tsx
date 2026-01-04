"use client";

import { useState, useMemo } from "react";
import { HistoryList } from "@/components/arbiter";
// import { HistoryDetail } from "@/components/arbiter"; // Disabled for build safety
import { MOCK_HISTORY, type HistoryEntry } from "@/lib/mock-history";
// import { Search, Filter, Download } from "lucide-react"; // Disabled for build safety
import { cn } from "@/lib/utils";

export default function HistoryPage() {
    const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedGame, setSelectedGame] = useState<string>("all");

    // For demo, use mock data - in production this would come from context/API
    const historyEntries = MOCK_HISTORY;

    // Filter logic
    const filteredEntries = useMemo(() => {
        return historyEntries.filter(entry => {
            const matchesSearch = entry.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
                entry.gameName.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesGame = selectedGame === "all" || entry.gameId === selectedGame;
            return matchesSearch && matchesGame;
        });
    }, [historyEntries, searchQuery, selectedGame]);

    // Unique games for filter
    const uniqueGames = useMemo(() => {
        const games = new Set(historyEntries.map(e => JSON.stringify({ id: e.gameId, name: e.gameName })));
        return Array.from(games).map(g => JSON.parse(g));
    }, [historyEntries]);

    // Export handler
    const handleExport = () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(filteredEntries, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "arbiter_history.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    return (
        <div className="min-h-[calc(100vh-5rem)] p-4 sm:p-6 pb-24 sm:pb-8">
            {/* Conditional rendering with smooth transitions */}
            {selectedEntry ? (
                // Detail View Placeholder (to be re-enabled)
                <div className="flex flex-col items-start gap-4">
                    <button
                        onClick={() => setSelectedEntry(null)}
                        className="px-4 py-2 bg-muted rounded hover:bg-muted/80"
                    >
                        ← Back
                    </button>
                    <div className="p-4 border rounded bg-card w-full">
                        <h2 className="text-xl font-bold">{selectedEntry.question}</h2>
                        <p className="text-muted-foreground">{selectedEntry.gameName}</p>
                        <div className="my-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded">
                            <p className="font-semibold text-emerald-600">Verdict:</p>
                            <p>{selectedEntry.verdict}</p>
                        </div>
                        <p className="text-sm text-muted-foreground italic">
                            (Full detail view temporarily disabled for maintenance)
                        </p>
                    </div>
                </div>
                /* 
                <HistoryDetail
                    entry={selectedEntry}
                    onBack={() => setSelectedEntry(null)}
                />
                */
            ) : (
                // List View
                <div className="animate-in fade-in duration-300 space-y-6">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight">History</h1>
                            <p className="mt-1 text-muted-foreground">
                                Your previous questions and answers
                            </p>
                        </div>

                        {/* Stats - visible on desktop */}
                        {historyEntries.length > 0 && (
                            <div className="hidden sm:flex items-center gap-4 text-sm text-muted-foreground bg-card border border-border px-4 py-2 rounded-lg">
                                <div className="flex items-center gap-2">
                                    <span className="font-bold">#</span>
                                    <span>{historyEntries.length} Questions</span>
                                </div>
                                <div className="w-px h-4 bg-border" />
                                <div>{uniqueGames.length} Games</div>
                            </div>
                        )}
                    </div>

                    {/* Search & Filter Bar */}
                    <div className="grid gap-3 sm:grid-cols-[1fr,200px,auto]">
                        {/* Search */}
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">🔍</span>
                            <input
                                type="text"
                                placeholder="Search questions..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full h-10 pl-9 pr-4 rounded-lg border border-border bg-card focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all placeholder:text-muted-foreground/70"
                            />
                        </div>

                        {/* Game Filter */}
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">🎮</span>
                            <select
                                value={selectedGame}
                                onChange={(e) => setSelectedGame(e.target.value)}
                                className="w-full h-10 pl-9 pr-8 rounded-lg border border-border bg-card focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 appearance-none cursor-pointer transition-all"
                            >
                                <option value="all">All Games</option>
                                {uniqueGames.map((game: any) => (
                                    <option key={game.id} value={game.id}>{game.name}</option>
                                ))}
                            </select>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-2">
                            <button
                                onClick={handleExport}
                                title="Export JSON"
                                className="h-10 w-10 flex items-center justify-center rounded-lg border border-border bg-card hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                            >
                                <span>⬇</span>
                            </button>
                        </div>
                    </div>

                    {/* Filter Status (Mobile) */}
                    <div className="sm:hidden text-xs text-muted-foreground flex justify-between px-1">
                        <span>{filteredEntries.length} results</span>
                        <span>{uniqueGames.length} games tracked</span>
                    </div>

                    {/* History List */}
                    <HistoryList
                        entries={filteredEntries}
                        onSelectEntry={setSelectedEntry}
                    />
                </div>
            )}
        </div>
    );
}
