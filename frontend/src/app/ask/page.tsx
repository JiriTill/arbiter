"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Loader2, Send, ArrowLeft, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
    QuoteCard,
    VerdictCard,
    GameSelector,
    RecentQuestions,
    LoadingRitual,
    SupersededCard,
    FeedbackWidget,
    OCRWarning,
    SourceSuggestionModal,
} from "@/components/arbiter";
import { cn } from "@/lib/utils";
import { askQuestion, listGames, ApiError, suggestSource } from "@/lib/api";
import type { AskResponse, AskState, Game as ApiGame, IndexingResponse } from "@/types/arbiter";

// Loading skeleton for results
function ResultSkeleton() {
    return (
        <div className="space-y-4 animate-pulse">
            {/* Verdict skeleton */}
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
                <div className="flex items-center gap-2">
                    <div className="h-5 w-5 rounded-full bg-muted" />
                    <div className="h-5 w-16 rounded bg-muted" />
                </div>
                <div className="space-y-2">
                    <div className="h-4 w-full rounded bg-muted" />
                    <div className="h-4 w-3/4 rounded bg-muted" />
                    <div className="h-4 w-1/2 rounded bg-muted" />
                </div>
            </div>

            {/* Quote skeleton */}
            <div className="rounded-lg border border-border bg-card p-4 space-y-3">
                <div className="h-4 w-24 rounded bg-muted" />
                <div className="space-y-2 pl-4 border-l-2 border-muted">
                    <div className="h-4 w-full rounded bg-muted" />
                    <div className="h-4 w-5/6 rounded bg-muted" />
                </div>
            </div>

            {/* Stats skeleton */}
            <div className="rounded-lg border border-border bg-card p-3">
                <div className="h-3 w-32 rounded bg-muted" />
            </div>
        </div>
    );
}

// Result display component
function ResultDisplay({
    result,
    onBack
}: {
    result: AskResponse;
    onBack: () => void;
}) {
    return (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-300">
            {/* Back button and question */}
            <div className="space-y-2">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onBack}
                    className="text-muted-foreground hover:text-foreground -ml-2"
                >
                    <ArrowLeft className="mr-1 h-4 w-4" />
                    Ask about {result.game_name}
                </Button>

                <div className="rounded-lg border border-border bg-card/50 p-3">
                    <p className="text-xs text-muted-foreground mb-1">
                        {result.game_name} {result.edition ? `(${result.edition})` : ""}
                    </p>
                    <p className="font-medium">{result.question}</p>
                </div>
            </div>

            {/* Verdict Card */}
            <VerdictCard
                verdict={result.verdict}
                confidence={result.confidence}
                gameName={result.game_name}
                question={result.question}
            />

            {/* Citations - simplified, merged into QuoteCard */}
            {result.citations.map((citation, idx) => (
                <QuoteCard
                    key={idx}
                    quote={citation.quote}
                    page={citation.page}
                    verified={citation.verified}
                    sourceId={citation.source_id}
                />
            ))}

            {/* Superseded Rule Warning */}
            {result.superseded_rule && (
                <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 delay-150">
                    <SupersededCard supersededRule={result.superseded_rule} />
                </div>
            )}

            {/* Feedback Widget */}
            <FeedbackWidget historyId={result.history_id} />

            {/* Response stats */}
            <div className="rounded-lg border border-border bg-card/50 p-3 text-center">
                <p className="text-xs text-muted-foreground">
                    Response generated in {result.response_time_ms}ms
                    {result.history_id && (
                        <span className="mx-2">•</span>
                    )}
                    {result.history_id && (
                        <span>Query #{result.history_id}</span>
                    )}
                </p>
            </div>
        </div>
    );
}

// Error display component
function ErrorDisplay({
    error,
    errorCode,
    onRetry
}: {
    error: string;
    errorCode?: string;
    onRetry: () => void;
}) {
    return (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 space-y-3 animate-in fade-in duration-200">
            <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                <div className="space-y-1">
                    <p className="font-medium text-destructive">
                        {errorCode === "NOT_INDEXED"
                            ? "Rules Not Available"
                            : "Something went wrong"}
                    </p>
                    <p className="text-sm text-muted-foreground">{error}</p>
                </div>
            </div>
            <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="w-full"
            >
                Try Again
            </Button>
        </div>
    );
}

// Indexing view with LoadingRitual
function IndexingView({
    indexingData,
    onComplete,
    onCancel,
}: {
    indexingData: IndexingResponse;
    onComplete: () => void;
    onCancel: () => void;
}) {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
            <LoadingRitual
                jobId={indexingData.job_id}
                gameName={indexingData.game_name}
                onComplete={onComplete}
                onError={(error) => console.error("Indexing error:", error)}
            />

            {/* Saved question reminder */}
            <div className="rounded-lg border border-border bg-card/50 p-4">
                <p className="text-sm text-muted-foreground mb-2">Your question:</p>
                <p className="font-medium">{indexingData.question}</p>
                <p className="text-xs text-muted-foreground mt-2">
                    We&apos;ll answer this as soon as indexing is complete.
                </p>
            </div>

            {/* Cancel option */}
            <Button
                variant="ghost"
                size="sm"
                onClick={onCancel}
                className="w-full text-muted-foreground"
            >
                Cancel and ask later
            </Button>
        </div>
    );
}

export default function AskPage() {
    const [selectedGame, setSelectedGame] = useState<ApiGame | null>(null);
    const [question, setQuestion] = useState("");
    const [askState, setAskState] = useState<AskState>({ status: "idle" });
    const [apiGames, setApiGames] = useState<ApiGame[]>([]);
    const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
    const [isSuggestionModalOpen, setIsSuggestionModalOpen] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Load games from API
    useEffect(() => {
        async function loadGames() {
            try {
                const response = await listGames();
                setApiGames(response.games);
            } catch (error) {
                console.error("Failed to load games:", error);
            }
        }
        loadGames();
    }, []);

    // Auto-resize textarea
    const adjustTextareaHeight = useCallback(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = "auto";
            const newHeight = Math.min(Math.max(textarea.scrollHeight, 120), 300);
            textarea.style.height = `${newHeight}px`;
        }
    }, []);

    useEffect(() => {
        adjustTextareaHeight();
    }, [question, adjustTextareaHeight]);

    const handleSubmit = async () => {
        if (!question.trim() || askState.status === "loading") return;

        // Need a game selected
        if (!selectedGame) {
            setAskState({
                status: "error",
                error: "Please select a game first",
                errorCode: "NO_GAME"
            });
            return;
        }

        setAskState({ status: "loading" });
        setPendingQuestion(question.trim());

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/ask`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        game_id: selectedGame.id,
                        edition: selectedGame.editions?.[0] || null,
                        question: question.trim(),
                    }),
                }
            );

            // Handle 202 Accepted (indexing in progress)
            if (response.status === 202) {
                const indexingData = await response.json() as IndexingResponse;
                setAskState({ status: "indexing", data: indexingData });
                return;
            }

            // Handle errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new ApiError(
                    errorData.error || `HTTP error ${response.status}`,
                    response.status,
                    errorData.error_code,
                    errorData.detail
                );
            }

            // Handle 200 OK (answer ready)
            const data = await response.json() as AskResponse;
            setAskState({ status: "success", data });
        } catch (error) {
            console.error("Error asking question:", error);

            if (error instanceof ApiError) {
                setAskState({
                    status: "error",
                    error: error.detail || error.message,
                    errorCode: error.errorCode
                });
            } else {
                setAskState({
                    status: "error",
                    error: "Failed to connect to the server. Please try again."
                });
            }
        }
    };

    // Handle indexing complete - retry the question
    const handleIndexingComplete = useCallback(async () => {
        if (!selectedGame || !pendingQuestion) return;

        setAskState({ status: "loading" });

        try {
            const response = await askQuestion({
                game_id: selectedGame.id,
                edition: selectedGame.editions?.[0] || null,
                question: pendingQuestion,
            });

            setAskState({ status: "success", data: response });
            setPendingQuestion(null);
        } catch (error) {
            console.error("Error asking question after indexing:", error);

            if (error instanceof ApiError) {
                setAskState({
                    status: "error",
                    error: error.detail || error.message,
                    errorCode: error.errorCode
                });
            } else {
                setAskState({
                    status: "error",
                    error: "Failed to get answer. Please try again."
                });
            }
        }
    }, [selectedGame, pendingQuestion]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleBack = () => {
        setAskState({ status: "idle" });
        setQuestion("");
        setPendingQuestion(null);
    };

    const handleRetry = () => {
        setAskState({ status: "idle" });
    };

    const handleCancelIndexing = () => {
        setAskState({ status: "idle" });
        setPendingQuestion(null);
    };

    const isLoading = askState.status === "loading";

    // OCR Logic
    const baseSources = selectedGame?.sources?.filter(s => s.expansion_id === null) || [];
    const expansionSources = selectedGame?.sources?.filter(s => s.expansion_id !== null) || [];

    const allNeedsOCR = baseSources.length > 0 && baseSources.every(s => s.needs_ocr);
    const someNeedsOCR = !allNeedsOCR && expansionSources.some(s => s.needs_ocr);

    const isSubmitDisabled = !question.trim() || isLoading || !selectedGame || allNeedsOCR;

    // Show indexing view
    if (askState.status === "indexing") {
        return (
            <div className="flex min-h-[calc(100vh-5rem)] flex-col p-4 sm:p-6">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold tracking-tight">Indexing Rules</h1>
                    <p className="mt-1 text-muted-foreground">
                        This happens once per game
                    </p>
                </div>

                <IndexingView
                    indexingData={askState.data}
                    onComplete={handleIndexingComplete}
                    onCancel={handleCancelIndexing}
                />
            </div>
        );
    }

    // Show result view when we have a successful response
    if (askState.status === "success") {
        return (
            <div className="flex min-h-[calc(100vh-5rem)] flex-col p-4 sm:p-6">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold tracking-tight">The Verdict</h1>
                    <p className="mt-1 text-muted-foreground">
                        Answer from The Arbiter
                    </p>
                </div>

                <ResultDisplay result={askState.data} onBack={handleBack} />
            </div>
        );
    }

    return (
        <div className="flex min-h-[calc(100vh-5rem)] flex-col p-4 sm:p-6 pb-24 sm:pb-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold tracking-tight">Ask The Arbiter</h1>
                <p className="mt-1 text-muted-foreground">
                    Get verified answers to your board game rules questions
                </p>
            </div>

            {/* Main Input Section */}
            <div className="space-y-4">
                {/* Step 1: Game Selector */}
                <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs flex items-center justify-center font-bold">1</span>
                        Select Game
                    </label>
                    <GameSelector
                        selectedGame={selectedGame}
                        onSelect={setSelectedGame}
                        games={apiGames}
                    />
                </div>

                {/* Step 2: Question Input */}
                {allNeedsOCR ? (
                    <OCRWarning
                        gameName={selectedGame?.name}
                        onSuggestSource={() => setIsSuggestionModalOpen(true)}
                    />
                ) : (
                    <div className="space-y-2">
                        {someNeedsOCR && (
                            <div className="rounded-md bg-amber-500/10 p-2 text-sm text-amber-400 border border-amber-500/20">
                                Note: Expansion rules not indexed yet (scanned PDF).
                            </div>
                        )}
                        <label
                            htmlFor="question"
                            className="text-sm font-medium text-muted-foreground flex items-center gap-2"
                        >
                            <span className={cn(
                                "w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold",
                                selectedGame
                                    ? "bg-emerald-500/20 text-emerald-400"
                                    : "bg-muted text-muted-foreground"
                            )}>2</span>
                            Your Question
                        </label>

                        {/* Disabled state when no game selected */}
                        {!selectedGame ? (
                            <div className="min-h-[120px] rounded-lg border-2 border-dashed border-border bg-muted/30 flex items-center justify-center p-6">
                                <p className="text-sm text-muted-foreground text-center">
                                    ↑ Select a game first to ask a question
                                </p>
                            </div>
                        ) : (
                            <Textarea
                                ref={textareaRef}
                                id="question"
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={`e.g., "Can I play a Knight before rolling?" or "How does the robber work?"`}
                                className={cn(
                                    "min-h-[120px] max-h-[300px] resize-none text-lg",
                                    "bg-card border-border focus-visible:ring-primary",
                                    "transition-all duration-200"
                                )}
                                disabled={isLoading}
                            />
                        )}

                        {/* Tip - hide on mobile */}
                        {selectedGame && !question && (
                            <div className="flex flex-wrap gap-2 pt-1 animate-in fade-in slide-in-from-top-1 duration-300">
                                <span className="text-xs text-muted-foreground self-center mr-1">Try asking:</span>
                                <button
                                    type="button"
                                    onClick={() => setQuestion("Can I play a Knight before rolling?")}
                                    className="text-xs bg-muted/50 hover:bg-muted px-2.5 py-1.5 rounded-full transition-colors text-foreground/80 border border-transparent hover:border-border"
                                >
                                    "Can I play a Knight before rolling?"
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setQuestion("How does the robber work?")}
                                    className="text-xs bg-muted/50 hover:bg-muted px-2.5 py-1.5 rounded-full transition-colors text-foreground/80 border border-transparent hover:border-border"
                                >
                                    "How does the robber work?"
                                </button>
                            </div>
                        )}

                        {selectedGame && (
                            <p className="text-xs text-muted-foreground hidden sm:block pt-1">
                                Tip: Press Ctrl+Enter to submit
                            </p>
                        )}
                    </div>
                )}

                {/* Error Display */}
                {askState.status === "error" && (
                    <ErrorDisplay
                        error={askState.error}
                        errorCode={askState.errorCode}
                        onRetry={handleRetry}
                    />
                )}

                {/* Loading Skeleton */}
                {isLoading && <ResultSkeleton />}

                {/* Submit Button */}
                {!isLoading && (
                    <Button
                        onClick={handleSubmit}
                        disabled={isSubmitDisabled}
                        className={cn(
                            "h-14 w-full text-lg font-semibold",
                            "transition-all duration-200",
                            !isSubmitDisabled && "bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/20"
                        )}
                        size="lg"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                Consulting the rulebook...
                            </>
                        ) : (
                            <>
                                <Send className="mr-2 h-5 w-5" />
                                Get Answer
                            </>
                        )}
                    </Button>
                )}
            </div>

            {/* Trust Badges - subtle inline chips */}
            {askState.status === "idle" && (
                <>
                    <div className="my-4 flex flex-wrap justify-center gap-2">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            Verified rulebooks
                        </span>
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs bg-muted text-muted-foreground border border-border">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Page citations
                        </span>
                    </div>

                    {/* Divider */}
                    <div className="my-2 border-t border-border" />

                    {/* Recent Questions */}
                    <div className="mt-4 flex-1">
                        <RecentQuestions
                            questions={[]}
                            onQuestionClick={(q) => {
                                setQuestion(q.question);
                            }}
                        />
                    </div>
                </>
            )}

            <SourceSuggestionModal
                isOpen={isSuggestionModalOpen}
                onClose={() => setIsSuggestionModalOpen(false)}
                onSubmit={async (url, note) => {
                    if (selectedGame) {
                        await suggestSource(selectedGame.id, url, note);
                    }
                }}
                gameName={selectedGame?.name || "this game"}
            />
        </div>
    );
}
