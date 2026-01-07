"use client";

import { useState, useRef, useEffect } from "react";
import { Search, X, Gamepad2, AlertTriangle, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Game } from "@/types/arbiter";

interface GameSelectorProps {
    selectedGame: Game | null;
    onSelect: (game: Game | null) => void;
    games?: Game[];
    className?: string;
}

// Game color generator based on name
function getGameColor(name: string): string {
    const colors = [
        "from-orange-500 to-red-600",
        "from-green-500 to-emerald-600",
        "from-sky-500 to-blue-600",
        "from-amber-500 to-yellow-600",
        "from-purple-500 to-violet-600",
        "from-pink-500 to-rose-600",
        "from-cyan-500 to-teal-600",
    ];
    const hash = name.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
}

export function GameSelector({ selectedGame, onSelect, games = [], className }: GameSelectorProps) {
    const [searchTerm, setSearchTerm] = useState("");
    const [isOpen, setIsOpen] = useState(false);
    const [highlightIndex, setHighlightIndex] = useState(-1);
    const inputRef = useRef<HTMLInputElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Filter games based on search term
    const filteredGames = games.filter((game) =>
        game.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Reset highlight when filtered games change
    useEffect(() => {
        setHighlightIndex(-1);
    }, [searchTerm]);

    // Handle keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "ArrowDown") {
            e.preventDefault();
            setHighlightIndex((prev) => Math.min(prev + 1, filteredGames.length - 1));
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setHighlightIndex((prev) => Math.max(prev - 1, -1));
        } else if (e.key === "Enter" && highlightIndex >= 0) {
            e.preventDefault();
            selectGame(filteredGames[highlightIndex]);
        } else if (e.key === "Escape") {
            setIsOpen(false);
            inputRef.current?.blur();
        }
    };

    const selectGame = (game: Game) => {
        onSelect(game);
        setSearchTerm("");
        setIsOpen(false);
    };

    const clearSelection = () => {
        onSelect(null);
        setSearchTerm("");
        inputRef.current?.focus();
    };

    // If game is selected, show the selected game badge
    if (selectedGame && !isOpen) {
        return (
            <div className={cn("relative", className)} ref={containerRef}>
                <div className="flex items-center gap-3 rounded-xl border-2 border-emerald-500/30 bg-emerald-500/10 p-3">
                    {/* Game avatar/image */}
                    {selectedGame.cover_image_url ? (
                        <img
                            src={selectedGame.cover_image_url}
                            alt={selectedGame.name}
                            className="w-12 h-12 rounded-xl object-cover shadow-lg"
                            onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                                (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                            }}
                        />
                    ) : null}
                    <div className={cn(
                        "w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center text-xl font-bold text-white shadow-lg",
                        getGameColor(selectedGame.name),
                        selectedGame.cover_image_url && "hidden"
                    )}>
                        {selectedGame.name.charAt(0).toUpperCase()}
                    </div>

                    {/* Game info */}
                    <div className="flex-1">
                        <div className="flex items-center gap-2">
                            <span className="font-semibold">{selectedGame.name}</span>
                            {selectedGame.sources?.some(s => s.needs_ocr) && (
                                <span title="OCR in progress">
                                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                                </span>
                            )}
                        </div>
                        {selectedGame.editions?.[0] && (
                            <span className="text-sm text-muted-foreground">{selectedGame.editions[0]}</span>
                        )}
                    </div>

                    {/* Change button */}
                    <button
                        type="button"
                        onClick={clearSelection}
                        className="p-2 rounded-lg hover:bg-background/50 transition text-muted-foreground hover:text-foreground"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={cn("relative", className)} ref={containerRef}>
            {/* Search Input */}
            <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground pointer-events-none" />
                <input
                    ref={inputRef}
                    type="text"
                    value={searchTerm}
                    onChange={(e) => {
                        setSearchTerm(e.target.value);
                        setIsOpen(true);
                    }}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={handleKeyDown}
                    placeholder="Search for a game..."
                    className={cn(
                        "w-full h-14 pl-12 pr-4 rounded-xl border-2 border-border bg-card text-lg",
                        "placeholder:text-muted-foreground",
                        "focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20",
                        "transition-all duration-200"
                    )}
                />
                {searchTerm && (
                    <button
                        type="button"
                        onClick={() => setSearchTerm("")}
                        className="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-muted"
                    >
                        <X className="h-4 w-4 text-muted-foreground" />
                    </button>
                )}
            </div>

            {/* Dropdown */}
            {isOpen && (
                <div className="absolute z-50 w-full mt-2 rounded-xl border border-border bg-card shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                    {/* Results */}
                    <div className="max-h-[300px] overflow-y-auto">
                        {filteredGames.length > 0 ? (
                            filteredGames.map((game, index) => {
                                const needsOCR = game.sources?.some(s => s.needs_ocr);
                                return (
                                    <button
                                        key={game.id}
                                        type="button"
                                        onClick={() => selectGame(game)}
                                        className={cn(
                                            "w-full flex items-center gap-3 p-3 text-left transition-colors",
                                            highlightIndex === index ? "bg-emerald-500/10" : "hover:bg-muted/50"
                                        )}
                                    >
                                        {/* Game avatar/image */}
                                        {game.cover_image_url ? (
                                            <img
                                                src={game.cover_image_url}
                                                alt={game.name}
                                                className="w-10 h-10 rounded-lg object-cover"
                                                onError={(e) => {
                                                    // Fallback to gradient on error
                                                    (e.target as HTMLImageElement).style.display = 'none';
                                                    (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                                                }}
                                            />
                                        ) : null}
                                        <div className={cn(
                                            "w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center text-lg font-bold text-white",
                                            getGameColor(game.name),
                                            game.cover_image_url && "hidden"
                                        )}>
                                            {game.name.charAt(0).toUpperCase()}
                                        </div>

                                        {/* Game info */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="font-medium truncate">{game.name}</span>
                                                {needsOCR && (
                                                    <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />
                                                )}
                                            </div>
                                            {game.editions?.[0] && (
                                                <span className="text-xs text-muted-foreground">{game.editions[0]}</span>
                                            )}
                                        </div>

                                        {/* Arrow */}
                                        <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    </button>
                                );
                            })
                        ) : (
                            <div className="p-6 text-center">
                                {searchTerm ? (
                                    <>
                                        <Gamepad2 className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                                        <p className="text-sm text-muted-foreground">No games found for "{searchTerm}"</p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Try a different search or request a new game
                                        </p>
                                    </>
                                ) : games.length === 0 ? (
                                    <>
                                        <Gamepad2 className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                                        <p className="text-sm text-muted-foreground">Loading games...</p>
                                    </>
                                ) : (
                                    <>
                                        <p className="text-sm text-muted-foreground">Type to search games</p>
                                    </>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Popular games hint */}
                    {!searchTerm && games.length > 0 && (
                        <div className="border-t border-border p-3 bg-muted/30">
                            <p className="text-xs text-muted-foreground text-center">
                                {games.length} games available • Start typing to search
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
