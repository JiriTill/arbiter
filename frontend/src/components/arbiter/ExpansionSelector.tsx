"use client";

import React, { useCallback, useState } from "react";
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragEndEvent,
} from "@dnd-kit/core";
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Check, ChevronDown, ChevronUp, Info } from "lucide-react";
import { useExpansions, ExpansionSelection } from "@/contexts/ExpansionContext";

/**
 * Sortable expansion item props
 */
interface SortableExpansionItemProps {
    selection: ExpansionSelection;
    onToggle: () => void;
}

/**
 * Individual sortable expansion item
 */
function SortableExpansionItem({ selection, onToggle }: SortableExpansionItemProps) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: selection.expansion.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    const { expansion, enabled } = selection;

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`
        flex items-center gap-3 p-3 rounded-lg border transition-all
        ${isDragging ? "z-50 shadow-lg scale-[1.02]" : ""}
        ${enabled
                    ? "bg-amber-50 border-amber-300 dark:bg-amber-900/20 dark:border-amber-700"
                    : "bg-white border-gray-200 dark:bg-gray-800 dark:border-gray-700"
                }
        hover:border-amber-400 dark:hover:border-amber-600
      `}
        >
            {/* Drag handle */}
            <button
                {...attributes}
                {...listeners}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-grab active:cursor-grabbing touch-none"
                aria-label="Drag to reorder"
            >
                <GripVertical className="w-5 h-5" />
            </button>

            {/* Checkbox */}
            <button
                onClick={onToggle}
                className={`
          w-5 h-5 rounded border-2 flex items-center justify-center transition-all
          ${enabled
                        ? "bg-amber-500 border-amber-500 text-white"
                        : "border-gray-300 dark:border-gray-600 hover:border-amber-400"
                    }
        `}
                aria-label={enabled ? `Disable ${expansion.name}` : `Enable ${expansion.name}`}
            >
                {enabled && <Check className="w-3 h-3" />}
            </button>

            {/* Expansion info */}
            <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {expansion.name}
                </div>
                {expansion.releaseDate && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                        Released: {new Date(expansion.releaseDate).getFullYear()}
                    </div>
                )}
            </div>

            {/* Priority indicator (only for enabled) */}
            {enabled && (
                <div className="px-2 py-1 text-xs font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 rounded">
                    #{selection.order + 1}
                </div>
            )}
        </div>
    );
}

/**
 * Expansion selector props
 */
interface ExpansionSelectorProps {
    className?: string;
}

/**
 * Expansion selector with drag-to-reorder
 */
export function ExpansionSelector({ className = "" }: ExpansionSelectorProps) {
    const {
        selections,
        toggleExpansion,
        reorderExpansions,
        hasEnabledExpansions,
        getEnabledExpansionIds,
    } = useExpansions();

    const [isCollapsed, setIsCollapsed] = useState(false);

    // DnD sensors
    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8, // Minimum drag distance before activating
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    /**
     * Handle drag end
     */
    const handleDragEnd = useCallback(
        (event: DragEndEvent) => {
            const { active, over } = event;

            if (over && active.id !== over.id) {
                const oldIndex = selections.findIndex(
                    (sel) => sel.expansion.id === active.id
                );
                const newIndex = selections.findIndex(
                    (sel) => sel.expansion.id === over.id
                );

                reorderExpansions(oldIndex, newIndex);
            }
        },
        [selections, reorderExpansions]
    );

    // No expansions available
    if (selections.length === 0) {
        return null;
    }

    const enabledCount = getEnabledExpansionIds().length;

    return (
        <div className={`rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 ${className}`}>
            {/* Header */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors rounded-t-xl"
            >
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                        Expansions
                    </span>
                    {enabledCount > 0 && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 rounded-full">
                            {enabledCount} selected
                        </span>
                    )}
                </div>

                {isCollapsed ? (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                )}
            </button>

            {/* Content */}
            {!isCollapsed && (
                <div className="p-4 pt-0 space-y-3">
                    {/* Info tooltip */}
                    <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-800 dark:text-blue-200">
                        <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <div>
                            <strong>Higher = Takes Precedence</strong>
                            <br />
                            Drag expansions to reorder. Rules from higher-ranked expansions override lower ones.
                        </div>
                    </div>

                    {/* Sortable list */}
                    <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={handleDragEnd}
                    >
                        <SortableContext
                            items={selections.map((s) => s.expansion.id)}
                            strategy={verticalListSortingStrategy}
                        >
                            <div className="space-y-2">
                                {selections.map((selection) => (
                                    <SortableExpansionItem
                                        key={selection.expansion.id}
                                        selection={selection}
                                        onToggle={() => toggleExpansion(selection.expansion.id)}
                                    />
                                ))}
                            </div>
                        </SortableContext>
                    </DndContext>

                    {/* Summary */}
                    {hasEnabledExpansions && (
                        <div className="pt-2 text-sm text-gray-500 dark:text-gray-400">
                            Priority order: {getEnabledExpansionIds().map((id, i) => {
                                const sel = selections.find(s => s.expansion.id === id);
                                return sel?.expansion.name;
                            }).join(" → ")}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default ExpansionSelector;
