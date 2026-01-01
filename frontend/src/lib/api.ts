/**
 * API client for The Arbiter backend.
 */

import type {
    AskRequest,
    AskResponse,
    AskErrorResponse,
    Game,
    GamesListResponse,
    FeedbackRequest,
    FeedbackResponse,
} from "@/types/arbiter";

// API Base URL from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// Error Handling
// ============================================================================

export class ApiError extends Error {
    constructor(
        message: string,
        public statusCode: number,
        public errorCode?: string,
        public detail?: string
    ) {
        super(message);
        this.name = "ApiError";
    }
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let errorData: AskErrorResponse | null = null;
        try {
            errorData = await response.json();
        } catch {
            // Response isn't JSON
        }

        throw new ApiError(
            errorData?.error || `HTTP error ${response.status}`,
            response.status,
            errorData?.error_code,
            errorData?.detail || undefined
        );
    }

    return response.json();
}

// ============================================================================
// Generic API Request
// ============================================================================

export async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
        ...options,
    });

    return handleResponse<T>(response);
}

// Convenience methods
export const api = {
    get: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: "GET" }),

    post: <T>(endpoint: string, data: unknown) =>
        apiRequest<T>(endpoint, {
            method: "POST",
            body: JSON.stringify(data),
        }),

    put: <T>(endpoint: string, data: unknown) =>
        apiRequest<T>(endpoint, {
            method: "PUT",
            body: JSON.stringify(data),
        }),

    delete: <T>(endpoint: string) =>
        apiRequest<T>(endpoint, { method: "DELETE" }),
};

// ============================================================================
// Ask API
// ============================================================================

/**
 * Ask a rules question about a board game.
 */
export async function askQuestion(request: AskRequest): Promise<AskResponse> {
    return api.post<AskResponse>("/ask", request);
}

/**
 * Send user feedback.
 */
export async function sendFeedback(request: FeedbackRequest): Promise<FeedbackResponse> {
    return api.post<FeedbackResponse>("/feedback", request);
}

// ============================================================================
// Games API
// ============================================================================

/**
 * List all available games.
 */
export async function listGames(
    search?: string,
    limit: number = 50,
    offset: number = 0
): Promise<GamesListResponse> {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    params.set("limit", limit.toString());
    params.set("offset", offset.toString());

    return api.get<GamesListResponse>(`/games?${params.toString()}`);
}

export async function getGame(gameId: number): Promise<Game> {
    return api.get<Game>(`/games/${gameId}`);
}

/**
 * Suggest a better source for a game.
 */
export async function suggestSource(
    gameId: number,
    url: string,
    note?: string
): Promise<{ success: boolean; suggestion_id: number; status: string }> {
    return api.post("/sources/suggest", {
        game_id: gameId,
        suggested_url: url,
        user_note: note,
    });
}

// ============================================================================
// Health API
// ============================================================================

interface HealthResponse {
    status: string;
    environment: string;
    version: string;
    timestamp: string;
}

/**
 * Check API health.
 */
export async function checkHealth(): Promise<HealthResponse> {
    return api.get<HealthResponse>("/health");
}
