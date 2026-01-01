"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";

/**
 * Expansion data type
 */
export interface Expansion {
    id: number;
    name: string;
    code: string;
    description?: string;
    releaseDate?: string;
    displayOrder?: number;
}

/**
 * Expansion selection with ordering
 */
export interface ExpansionSelection {
    expansion: Expansion;
    enabled: boolean;
    order: number;
}

/**
 * Expansion context state
 */
interface ExpansionContextState {
    // Available expansions for current game
    expansions: Expansion[];
    setExpansions: (expansions: Expansion[]) => void;

    // Selected expansions with priority order
    selections: ExpansionSelection[];

    // Toggle expansion on/off
    toggleExpansion: (expansionId: number) => void;

    // Reorder expansions (drag and drop)
    reorderExpansions: (fromIndex: number, toIndex: number) => void;

    // Get ordered list of enabled expansion IDs
    getEnabledExpansionIds: () => number[];

    // Reset selections
    resetSelections: () => void;

    // Is any expansion enabled?
    hasEnabledExpansions: boolean;
}

const ExpansionContext = createContext<ExpansionContextState | null>(null);

/**
 * Hook to use expansion context
 */
export function useExpansions(): ExpansionContextState {
    const context = useContext(ExpansionContext);
    if (!context) {
        throw new Error("useExpansions must be used within ExpansionProvider");
    }
    return context;
}

/**
 * Provider props
 */
interface ExpansionProviderProps {
    children: ReactNode;
}

/**
 * Expansion context provider
 */
export function ExpansionProvider({ children }: ExpansionProviderProps) {
    const [expansions, setExpansionsState] = useState<Expansion[]>([]);
    const [selections, setSelections] = useState<ExpansionSelection[]>([]);

    /**
     * Set available expansions and initialize selections
     */
    const setExpansions = useCallback((newExpansions: Expansion[]) => {
        setExpansionsState(newExpansions);

        // Initialize selections with all disabled, ordered by release date (newest first)
        const sorted = [...newExpansions].sort((a, b) => {
            if (a.releaseDate && b.releaseDate) {
                return new Date(b.releaseDate).getTime() - new Date(a.releaseDate).getTime();
            }
            return (a.displayOrder || 0) - (b.displayOrder || 0);
        });

        setSelections(
            sorted.map((exp, index) => ({
                expansion: exp,
                enabled: false,
                order: index,
            }))
        );
    }, []);

    /**
     * Toggle expansion enabled state
     */
    const toggleExpansion = useCallback((expansionId: number) => {
        setSelections((prev) =>
            prev.map((sel) =>
                sel.expansion.id === expansionId
                    ? { ...sel, enabled: !sel.enabled }
                    : sel
            )
        );
    }, []);

    /**
     * Reorder expansions by moving from one index to another
     */
    const reorderExpansions = useCallback((fromIndex: number, toIndex: number) => {
        if (fromIndex === toIndex) return;

        setSelections((prev) => {
            const newSelections = [...prev];
            const [removed] = newSelections.splice(fromIndex, 1);
            newSelections.splice(toIndex, 0, removed);

            // Update order numbers
            return newSelections.map((sel, index) => ({
                ...sel,
                order: index,
            }));
        });
    }, []);

    /**
     * Get ordered list of enabled expansion IDs
     * Order matters - higher in list = takes precedence
     */
    const getEnabledExpansionIds = useCallback(() => {
        return selections
            .filter((sel) => sel.enabled)
            .sort((a, b) => a.order - b.order)
            .map((sel) => sel.expansion.id);
    }, [selections]);

    /**
     * Reset all selections
     */
    const resetSelections = useCallback(() => {
        setSelections((prev) =>
            prev.map((sel) => ({ ...sel, enabled: false }))
        );
    }, []);

    /**
     * Check if any expansion is enabled
     */
    const hasEnabledExpansions = selections.some((sel) => sel.enabled);

    const value: ExpansionContextState = {
        expansions,
        setExpansions,
        selections,
        toggleExpansion,
        reorderExpansions,
        getEnabledExpansionIds,
        resetSelections,
        hasEnabledExpansions,
    };

    return (
        <ExpansionContext.Provider value={value}>
            {children}
        </ExpansionContext.Provider>
    );
}
