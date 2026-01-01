/**
 * Server-Sent Events (SSE) client utilities for real-time updates.
 */

export interface IngestionProgress {
    state: string;
    pct: number;
    msg: string;
    result?: Record<string, unknown>;
    error?: string;
}

export type IngestionEventType = "progress" | "complete" | "error";

export interface IngestionEventHandler {
    onProgress?: (data: IngestionProgress) => void;
    onComplete?: (data: IngestionProgress) => void;
    onError?: (data: IngestionProgress) => void;
    onDisconnect?: () => void;
    onReconnect?: () => void;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Connect to ingestion progress SSE endpoint.
 * 
 * @param jobId - The job ID to watch
 * @param handlers - Event handlers for different event types
 * @returns Cleanup function to close the connection
 */
export function connectToIngestionProgress(
    jobId: string,
    handlers: IngestionEventHandler
): () => void {
    const url = `${API_BASE_URL}/ingest/${jobId}/events`;
    let eventSource: EventSource | null = null;
    let reconnectAttempts = 0;
    let shouldClose = false;
    const MAX_RECONNECT_ATTEMPTS = 3;
    const RECONNECT_DELAY = 2000;

    function connect() {
        if (shouldClose) return;

        eventSource = new EventSource(url);

        eventSource.addEventListener("progress", (event) => {
            reconnectAttempts = 0; // Reset on successful message
            const data = JSON.parse(event.data) as IngestionProgress;
            handlers.onProgress?.(data);
        });

        eventSource.addEventListener("complete", (event) => {
            const data = JSON.parse(event.data) as IngestionProgress;
            handlers.onComplete?.(data);
            // Close connection on complete
            eventSource?.close();
        });

        eventSource.addEventListener("error", (event) => {
            // Check if it's an SSE event with data
            if ((event as MessageEvent).data) {
                const data = JSON.parse((event as MessageEvent).data) as IngestionProgress;
                handlers.onError?.(data);
                eventSource?.close();
                return;
            }

            // Otherwise it's a connection error
            console.warn("SSE connection error, attempting reconnect...");
            handlers.onDisconnect?.();
            eventSource?.close();

            // Attempt reconnect
            if (!shouldClose && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                setTimeout(() => {
                    handlers.onReconnect?.();
                    connect();
                }, RECONNECT_DELAY * reconnectAttempts);
            }
        });

        // Handle generic open event
        eventSource.onopen = () => {
            reconnectAttempts = 0;
        };
    }

    connect();

    // Return cleanup function
    return () => {
        shouldClose = true;
        eventSource?.close();
    };
}

/**
 * Get human-readable stage name from state.
 */
export function getStageLabel(state: string): string {
    const stages: Record<string, string> = {
        queued: "Preparing...",
        downloading: "Fetching official rules...",
        extracting: "Extracting text from PDF...",
        chunking: "Creating searchable chunks...",
        embedding: "Indexing with AI...",
        saving: "Almost ready...",
        ready: "Ready to answer questions!",
        failed: "Something went wrong",
        error: "Something went wrong",
        unknown: "Checking status...",
    };

    return stages[state] || state;
}

/**
 * Get stage index for animation purposes.
 */
export function getStageIndex(state: string): number {
    const order = ["queued", "downloading", "extracting", "chunking", "embedding", "saving", "ready"];
    const index = order.indexOf(state);
    return index >= 0 ? index : 0;
}
