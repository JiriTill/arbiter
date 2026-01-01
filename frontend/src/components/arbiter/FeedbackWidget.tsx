"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FeedbackModal } from "./FeedbackModal";
import { sendFeedback } from "@/lib/api";
import { FeedbackType } from "@/types/arbiter";

interface FeedbackWidgetProps {
    historyId: number | null;
}

export function FeedbackWidget({ historyId }: FeedbackWidgetProps) {
    const [hasVoted, setHasVoted] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [showToast, setShowToast] = useState(false);

    if (!historyId) return null;

    const handleVote = async (type: "up" | "down") => {
        if (type === "up") {
            try {
                await sendFeedback({
                    ask_history_id: historyId,
                    feedback_type: "helpful",
                });
                setHasVoted(true);
                showThanks();
            } catch (e) {
                console.error("Failed to send feedback:", e);
            }
        } else {
            setShowModal(true);
        }
    };

    const handleModalSubmit = async (type: FeedbackType, note: string) => {
        try {
            await sendFeedback({
                ask_history_id: historyId,
                feedback_type: type,
                user_note: note,
            });
            setHasVoted(true);
            showThanks();
        } catch (e) {
            console.error("Failed to send feedback:", e);
        }
    };

    const showThanks = () => {
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
    };

    if (hasVoted && !showToast) {
        return (
            <div className="text-center text-sm text-green-500 py-4 font-medium animate-in fade-in">
                Thanks for your feedback!
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center gap-2 py-6 border-t border-white/5 mt-8 w-full">
            <span className="text-sm text-muted-foreground">Was this helpful?</span>
            <div className="flex gap-4">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleVote("up")}
                    className="gap-2 min-w-[80px] hover:bg-green-500/10 hover:text-green-500 hover:border-green-500/50 transition-colors bg-black/20 border-white/10"
                >
                    <ThumbsUp className="h-4 w-4" />
                    Yes
                </Button>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleVote("down")}
                    className="gap-2 min-w-[80px] hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/50 transition-colors bg-black/20 border-white/10"
                >
                    <ThumbsDown className="h-4 w-4" />
                    No
                </Button>
            </div>

            <FeedbackModal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                onSubmit={handleModalSubmit}
            />

            {showToast && (
                <div className="fixed bottom-6 right-6 bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg shadow-black/50 animate-in slide-in-from-bottom-5 fade-in duration-300 z-50 flex items-center gap-2">
                    <ThumbsUp className="h-4 w-4" />
                    <span>Thanks for your feedback!</span>
                </div>
            )}
        </div>
    );
}
