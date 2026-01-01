"use client";

import { useState } from "react";
import { ChevronDown, Gamepad2, X, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Game } from "@/types/arbiter";

interface GameSelectorProps {
    selectedGame: Game | null;
    onSelect: (game: Game | null) => void;
    games?: Game[];
    className?: string;
}

// Placeholder games for UI development (used when no games prop provided)
const PLACEHOLDER_GAMES: Game[] = [];

export function GameSelector({ selectedGame, onSelect, games, className }: GameSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);

    // Use provided games or fallback to placeholders
    const displayGames = games && games.length > 0 ? games : PLACEHOLDER_GAMES;

    return (
        <>
            {/* Trigger Button */}
            <button
                type="button"
                onClick={() => setIsOpen(true)}
                className={cn(
                    "flex w-full items-center justify-between gap-3 rounded-lg border border-border bg-card p-4 text-left transition-colors hover:bg-card/80 active:bg-card/70",
                    "min-h-[56px]", // Large tap target
                    className
                )}
            >
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                        <Gamepad2 className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                        {selectedGame ? (
                            <>
                                <div className="flex items-center gap-2">
                                    <p className="font-medium">{selectedGame.name}</p>
                                    {selectedGame.sources?.some(s => s.needs_ocr) && (
                                        <div title="OCR support coming soon. Manual verification recommended.">
                                            <AlertTriangle className="h-4 w-4 text-amber-500" />
                                        </div>
                                    )}
                                </div>
                                {selectedGame.editions && selectedGame.editions.length > 0 && (
                                    <p className="text-sm text-muted-foreground">{selectedGame.editions[0]}</p>
                                )}
                            </>
                        ) : (
                            <p className="text-muted-foreground">Select a game...</p>
                        )}
                    </div>
                </div>
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
            </button>

            {/* Modal/Sheet Overlay */}
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Sheet Content */}
                    <div className="relative z-10 max-h-[80vh] w-full max-w-md overflow-hidden rounded-t-2xl bg-background sm:rounded-2xl">
                        {/* Header */}
                        <div className="flex items-center justify-between border-b border-border p-4">
                            <h2 className="text-lg font-semibold">Select Game</h2>
                            <button
                                type="button"
                                onClick={() => setIsOpen(false)}
                                className="flex h-10 w-10 items-center justify-center rounded-lg hover:bg-muted"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        {/* Game List */}
                        <div className="max-h-[60vh] overflow-y-auto p-2">
                            {/* No game option */}
                            <button
                                type="button"
                                onClick={() => {
                                    onSelect(null);
                                    setIsOpen(false);
                                }}
                                className={cn(
                                    "flex w-full items-center gap-3 rounded-lg p-3 text-left transition-colors hover:bg-muted",
                                    !selectedGame && "bg-muted"
                                )}
                            >
                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background border border-border">
                                    <Gamepad2 className="h-5 w-5 text-muted-foreground" />
                                </div>
                                <div>
                                    <p className="font-medium">No game selected</p>
                                    <p className="text-sm text-muted-foreground">Ask a general question</p>
                                </div>
                            </button>

                            {/* Divider */}
                            <div className="my-2 border-t border-border" />

                            {/* Games */}
                            {displayGames.map((game) => {
                                const needsOCR = game.sources?.some(s => s.needs_ocr);
                                return (
                                    <button
                                        key={game.id}
                                        type="button"
                                        onClick={() => {
                                            onSelect(game);
                                            setIsOpen(false);
                                        }}
                                        className={cn(
                                            "flex w-full items-center gap-3 rounded-lg p-3 text-left transition-colors hover:bg-muted",
                                            selectedGame?.id === game.id && "bg-primary/10"
                                        )}
                                    >
                                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                                            <Gamepad2 className="h-5 w-5 text-muted-foreground" />
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <p className="font-medium">{game.name}</p>
                                                {needsOCR && (
                                                    <div title="OCR support coming soon. Manual verification recommended.">
                                                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                                                    </div>
                                                )}
                                            </div>
                                            {(game.editions || [])[0] && (
                                                <p className="text-sm text-muted-foreground">{(game.editions || [])[0]}</p>
                                            )}
                                        </div>
                                        {selectedGame?.id === game.id && (
                                            <div className="h-2 w-2 rounded-full bg-primary" />
                                        )}
                                    </button>
                                );
                            })}
                        </div>

                        {/* Footer hint */}
                        <div className="border-t border-border p-4">
                            <p className="text-center text-sm text-muted-foreground">
                                Upload your own rulebook in Profile
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
