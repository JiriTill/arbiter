"use client";

import { useState } from "react";
import { X, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type FeedbackType = "wrong_quote" | "wrong_interpretation" | "missing_context" | "wrong_source";

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (type: FeedbackType, note: string) => void;
}

const FEEDBACK_OPTIONS: { id: FeedbackType; label: string }[] = [
    { id: "wrong_quote", label: "Quote doesn't match rules" },
    { id: "wrong_interpretation", label: "Interpretation is wrong" },
    { id: "missing_context", label: "Missing important context" },
    { id: "wrong_source", label: "Wrong source cited" },
];

export function FeedbackModal({ isOpen, onClose, onSubmit }: FeedbackModalProps) {
    const [selectedType, setSelectedType] = useState<FeedbackType | null>(null);
    const [note, setNote] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!selectedType) return;
        setIsSubmitting(true);
        await onSubmit(selectedType, note);
        setIsSubmitting(false);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-md rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-6 shadow-xl animate-in zoom-in-95 duration-200 m-4">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-foreground">
                        What seems to be the issue?
                    </h3>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                        onClick={onClose}
                    >
                        <X className="h-4 w-4" />
                    </Button>
                </div>

                <div className="space-y-3 mb-6">
                    {FEEDBACK_OPTIONS.map((option) => (
                        <button
                            key={option.id}
                            onClick={() => setSelectedType(option.id)}
                            className={cn(
                                "w-full flex items-center justify-between rounded-md border p-3 text-sm transition-colors",
                                selectedType === option.id
                                    ? "bg-[#fbbf24]/10 border-[#fbbf24] text-[#fbbf24]"
                                    : "bg-transparent border-[#2a2a2a] text-muted-foreground hover:bg-[#2a2a2a] hover:text-foreground"
                            )}
                        >
                            <span>{option.label}</span>
                            {selectedType === option.id && <Check className="h-4 w-4" />}
                        </button>
                    ))}
                </div>

                <div className="space-y-2 mb-6">
                    <label className="text-xs font-medium text-muted-foreground">
                        Additional Details (Optional)
                    </label>
                    <textarea
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        placeholder="Tell us more about what's wrong..."
                        className="w-full min-h-[80px] rounded-md border border-[#2a2a2a] bg-[#111111] p-3 text-sm text-foreground focus:border-[#fbbf24] focus:outline-none placeholder:text-muted-foreground/50 resize-y"
                    />
                </div>

                <div className="flex justify-end gap-2">
                    <Button variant="ghost" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        disabled={!selectedType || isSubmitting}
                        onClick={handleSubmit}
                        className={cn(
                            "bg-[#fbbf24] text-black hover:bg-[#d97706]",
                            !selectedType && "opacity-50 cursor-not-allowed"
                        )}
                    >
                        {isSubmitting ? "Sending..." : "Submit Feedback"}
                    </Button>
                </div>
            </div>
        </div>
    );
}
