
import { AlertCircle } from "lucide-react";

interface OCRWarningProps {
    gameName?: string;
    onSuggestSource?: () => void;
}

export function OCRWarning({ gameName, onSuggestSource }: OCRWarningProps) {
    return (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                    <p className="font-medium text-amber-900">
                        {gameName ? `${gameName}'s rulebook appears to be a scanned PDF.` : "Scanned PDF detected."}
                    </p>
                    <p className="text-sm text-amber-800">
                        We can&apos;t index scanned documents yet, but OCR support is coming in Phase 3!
                    </p>
                </div>
            </div>
            {onSuggestSource && (
                <div className="flex gap-4 pl-8 text-sm">
                    <button
                        onClick={onSuggestSource}
                        className="text-amber-700 underline hover:text-amber-900"
                    >
                        Suggest a better source
                    </button>
                </div>
            )}
        </div>
    );
}
