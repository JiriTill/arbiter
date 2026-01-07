"use client";

import { useState, useMemo, useEffect } from "react";
import { HistoryList } from "@/components/arbiter";
import { getHistory, type HistoryEntry as ApiHistoryEntry } from "@/lib/api";
import { cn } from "@/lib/utils";

// Adapter type to match the HistoryList component expectations
interface HistoryEntry {
    id: string;
    question: string;
    gameId: string;
    gameName: string;
    gameEdition: string;
    timestamp: Date;
    verdict: string;
    confidence: "high" | "medium" | "low";
    quote: string;
    quotePage: number;
    quoteVerified: boolean;
    sourceType: "rulebook" | "faq" | "errata";
    sourceEdition: string;
    sourceUrl?: string;
    superseded?: {
        oldQuote: string;
        oldPage: number;
        reason: string;
    };
}

// Convert API response to component format
function convertApiEntry(entry: ApiHistoryEntry): HistoryEntry {
    const firstCitation = entry.citations?.[0];

    return {
        id: entry.id.toString(),
        question: entry.question,
        gameId: entry.game_id.toString(),
        gameName: entry.game_name,
        gameEdition: entry.edition || "Unknown Edition",
        timestamp: new Date(entry.created_at),
        verdict: entry.verdict,
        confidence: entry.confidence,
        quote: firstCitation?.quote || "No citation available",
        quotePage: firstCitation?.page || 0,
        quoteVerified: firstCitation?.verified || false,
        sourceType: (firstCitation?.source_type as "rulebook" | "faq" | "errata") || "rulebook",
        sourceEdition: entry.edition || "Unknown",
    };
}

export default function HistoryPage() {
    const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedGame, setSelectedGame] = useState<string>("all");
    const [historyEntries, setHistoryEntries] = useState<HistoryEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch history from API
    useEffect(() => {
        async function fetchHistory() {
            setLoading(true);
            setError(null);
            try {
                const response = await getHistory(undefined, 100, 0);
                const entries = response.items.map(convertApiEntry);
                setHistoryEntries(entries);
            } catch (err) {
                console.error("Failed to fetch history:", err);
                setError("Failed to load history. Please try again later.");
                setHistoryEntries([]);
            } finally {
                setLoading(false);
            }
        }
        fetchHistory();
    }, []);

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
                // Detail View
                <div className="flex flex-col items-start gap-4 animate-in fade-in duration-300">
                    <button
                        onClick={() => setSelectedEntry(null)}
                        className="px-4 py-2 bg-muted rounded hover:bg-muted/80 transition-colors"
                    >
                        ← Back to History
                    </button>
                    <div className="p-6 border rounded-lg bg-card w-full space-y-4">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span className="px-2 py-1 bg-muted rounded">{selectedEntry.gameName}</span>
                            <span>•</span>
                            <span>{selectedEntry.gameEdition}</span>
                        </div>
                        <h2 className="text-xl font-bold">{selectedEntry.question}</h2>

                        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="font-semibold text-emerald-600">Verdict</span>
                                <span className={cn(
                                    "px-2 py-0.5 rounded text-xs font-medium",
                                    selectedEntry.confidence === "high" && "bg-emerald-500/20 text-emerald-600",
                                    selectedEntry.confidence === "medium" && "bg-amber-500/20 text-amber-600",
                                    selectedEntry.confidence === "low" && "bg-red-500/20 text-red-600",
                                )}>
                                    {selectedEntry.confidence} confidence
                                </span>
                            </div>
                            <p className="text-foreground">{selectedEntry.verdict}</p>
                        </div>

                        {selectedEntry.quote && (
                            <div className="p-4 bg-muted/50 border border-border rounded-lg">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-sm font-medium text-muted-foreground">Citation</span>
                                    {selectedEntry.quoteVerified && (
                                        <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-600">✓ Verified</span>
                                    )}
                                </div>
                                <blockquote className="italic text-foreground/80 border-l-2 border-emerald-500 pl-3">
                                    "{selectedEntry.quote}"
                                </blockquote>
                                <p className="mt-2 text-sm text-muted-foreground">
                                    — {selectedEntry.sourceEdition}, Page {selectedEntry.quotePage}
                                </p>
                            </div>
                        )}

                        <div className="text-xs text-muted-foreground">
                            Asked {selectedEntry.timestamp.toLocaleDateString()} at {selectedEntry.timestamp.toLocaleTimeString()}
                        </div>
                    </div>
                </div>
            ) : (
                // List View
                <div className="animate-in fade-in duration-300 space-y-6">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight">History</h1>
                            <p className="mt-1 text-muted-foreground">
                                All questions and answers from the community
                            </p>
                        </div>

                        {/* Stats - visible on desktop */}
                        {!loading && historyEntries.length > 0 && (
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

                    {/* Loading State */}
                    {loading && (
                        <div className="flex items-center justify-center py-12">
                            <div className="flex items-center gap-3 text-muted-foreground">
                                <div className="animate-spin h-5 w-5 border-2 border-emerald-500 border-t-transparent rounded-full" />
                                <span>Loading history...</span>
                            </div>
                        </div>
                    )}

                    {/* Error State */}
                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-600">
                            {error}
                        </div>
                    )}

                    {/* Empty State */}
                    {!loading && !error && historyEntries.length === 0 && (
                        <div className="text-center py-12 text-muted-foreground">
                            <div className="text-4xl mb-4">📭</div>
                            <h3 className="text-lg font-medium">No history yet</h3>
                            <p className="mt-1">Ask a question to see it appear here!</p>
                        </div>
                    )}

                    {/* Search & Filter Bar */}
                    {!loading && historyEntries.length > 0 && (
                        <>
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
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
