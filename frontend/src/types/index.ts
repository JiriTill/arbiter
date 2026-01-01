// Shared TypeScript types for The Arbiter
// These types are designed to be compatible with the FastAPI backend

export interface Game {
    id: string;
    name: string;
    slug: string;
    coverImage?: string;
    rulebookUrl?: string;
    createdAt: string;
    updatedAt: string;
}

export interface Question {
    id: string;
    gameId: string;
    question: string;
    createdAt: string;
}

export interface Citation {
    pageNumber: number;
    text: string;
    confidence: number; // 0-1 score
}

export interface Answer {
    id: string;
    questionId: string;
    answer: string;
    citations: Citation[];
    verificationStatus: "verified" | "ambiguous" | "not_found";
    createdAt: string;
}

export interface HistoryItem {
    id: string;
    question: Question;
    answer?: Answer;
    game: Game;
}

// API Response types
export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
}

export interface AskRequest {
    gameId: string;
    question: string;
}

export interface AskResponse {
    questionId: string;
    answer: Answer;
}
