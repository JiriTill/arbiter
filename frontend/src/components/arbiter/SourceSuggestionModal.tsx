import { useState } from "react";
import { Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface SourceSuggestionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (url: string, note?: string) => Promise<void>;
    gameName: string;
}

export function SourceSuggestionModal({ isOpen, onClose, onSubmit, gameName }: SourceSuggestionModalProps) {
    const [url, setUrl] = useState("");
    const [note, setNote] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await onSubmit(url, note);
            onClose();
            setUrl("");
            setNote("");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-in fade-in duration-200">
            <div className="bg-background rounded-lg shadow-lg w-full max-w-md border border-border p-6 space-y-4">
                <div className="flex justify-between items-start">
                    <div className="space-y-1">
                        <h2 className="text-lg font-semibold">Suggest Better Source</h2>
                        <p className="text-sm text-muted-foreground">
                            Found a better version of the rules (e.g. text-based PDF or HTML) for {gameName}?
                        </p>
                    </div>
                    <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
                        <X className="h-4 w-4" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <label htmlFor="url" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Source URL</label>
                        <input
                            id="url"
                            type="url"
                            placeholder="https://..."
                            required
                            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <label htmlFor="note" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Notes (optional)</label>
                        <Textarea
                            id="note"
                            placeholder="Any details about this source..."
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                        />
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                        <Button type="button" variant="outline" onClick={onClose}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Submit Suggestion
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
