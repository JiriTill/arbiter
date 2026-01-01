/**
 * Arbiter API types matching the backend schema.
 */

// ============================================================================
// Request Types
// ============================================================================

export interface AskRequest {
    game_id: number;
    edition?: string | null;
    question: string;
    expansion_ids?: number[];
}

// ============================================================================
// Response Types
// ============================================================================

export interface Citation {
    chunk_id: number;
    quote: string;
    page: number;
    source_type: "rulebook" | "faq" | "errata";
    verified: boolean;
    source_id?: number | null;
}

export type Confidence = "high" | "medium" | "low";

/**
 * Superseded rule info when expansion overrides base
 */
export interface SupersededRule {
    quote: string;
    page: number;
    source_type: "rulebook" | "faq" | "errata";
    reason: string;
    confidence?: number;
}

export interface AskResponse {
    success: boolean;
    verdict: string;
    confidence: Confidence;
    confidence_reason?: string;
    citations: Citation[];
    game_name: string;
    edition: string | null;
    question: string;
    history_id: number | null;
    response_time_ms: number;
    superseded_rule?: SupersededRule;
    conflict_note?: string;
    notes?: string[];
}

export type FeedbackType = "helpful" | "wrong_quote" | "wrong_interpretation" | "missing_context" | "wrong_source";

export interface FeedbackRequest {
    ask_history_id: number;
    feedback_type: FeedbackType;
    selected_chunk_id?: number | null;
    user_note?: string;
}

export interface FeedbackResponse {
    success: boolean;
    feedback_id: number;
}

export interface AskErrorResponse {
    success: false;
    error: string;
    error_code: string;
    detail?: string;
}

/**
 * 202 Response when sources need indexing
 */
export interface IndexingResponse {
    status: "indexing";
    job_id: string;
    job_ids: string[];
    status_url: string | null;
    sources_to_index: number;
    estimated_seconds: number;
    message: string;
    game_name: string;
    edition: string | null;
    question: string;
}

export interface Expansion {
    id: number;
    name: string;
    code: string;
    description?: string;
    releaseDate?: string;
    displayOrder?: number;
}

export interface GameSource {
    id: number;
    source_type: string;
    edition: string;
    needs_ocr: boolean;
    expansion_id: number | null;
}

export interface Game {
    id: number;
    name: string;
    slug: string;
    bgg_id: number | null;
    cover_image_url: string | null;
    editions: string[];
    has_indexed_sources: boolean;
    expansions?: Expansion[];
    sources?: GameSource[];
}

export interface GamesListResponse {
    games: Game[];
    total: number;
}

// ============================================================================
// UI State Types
// ============================================================================

export type AskState =
    | { status: "idle" }
    | { status: "loading" }
    | { status: "indexing"; data: IndexingResponse }
    | { status: "success"; data: AskResponse }
    | { status: "error"; error: string; errorCode?: string };

// ============================================================================
// Component Props Types
// ============================================================================

export interface VerdictDisplayProps {
    verdict: string;
    confidence: Confidence;
    citations: Citation[];
    gameName: string;
    edition?: string | null;
    question: string;
    responseTimeMs: number;
}
