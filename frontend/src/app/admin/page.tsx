"use client";

import { useState, useEffect, useCallback } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Game {
    id: number;
    name: string;
    slug: string;
    bgg_id: number | null;
    cover_image_url: string | null;
    sources?: Source[];
}

interface Source {
    id: number;
    game_id: number;
    edition: string;
    source_type: string;
    source_url: string;
    is_official: boolean;
    needs_ocr: boolean;
    last_ingested_at: string | null;
}

export default function AdminPage() {
    const [games, setGames] = useState<Game[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Form states
    const [showGameForm, setShowGameForm] = useState(false);
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [selectedGameId, setSelectedGameId] = useState<number | null>(null);

    // New game form
    const [newGame, setNewGame] = useState({
        name: "",
        slug: "",
        bgg_id: "",
        cover_image_url: "",
    });

    // Upload form
    const [uploadData, setUploadData] = useState({
        game_id: "",
        edition: "1st Edition",
        source_type: "rulebook",
        needs_ocr: false,
    });
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState<string>("");

    const fetchGames = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/admin/games`);
            if (!res.ok) throw new Error("Failed to fetch games");
            const data = await res.json();
            setGames(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchGames();
    }, [fetchGames]);

    const handleCreateGame = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append("name", newGame.name);
            formData.append("slug", newGame.slug);
            if (newGame.bgg_id) formData.append("bgg_id", newGame.bgg_id);
            if (newGame.cover_image_url) formData.append("cover_image_url", newGame.cover_image_url);

            const res = await fetch(`${API_BASE_URL}/admin/games`, {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to create game");
            }

            setShowGameForm(false);
            setNewGame({ name: "", slug: "", bgg_id: "", cover_image_url: "" });
            fetchGames();
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to create game");
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!uploadFile) {
            alert("Please select a PDF file");
            return;
        }

        setUploading(true);
        setUploadProgress("Uploading PDF...");

        try {
            const formData = new FormData();
            formData.append("game_id", uploadData.game_id);
            formData.append("edition", uploadData.edition);
            formData.append("source_type", uploadData.source_type);
            formData.append("needs_ocr", String(uploadData.needs_ocr));
            formData.append("file", uploadFile);

            const res = await fetch(`${API_BASE_URL}/admin/sources/upload`, {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Upload failed");
            }

            const result = await res.json();
            setUploadProgress(`✅ Uploaded! ${result.file_size_mb} MB. Source ID: ${result.source.id}`);

            // Trigger processing immediately if needed
            if (uploadData.needs_ocr) {
                setUploadProgress("Triggering OCR processing...");
                await handleProcess(result.source.id);
                setUploadProgress("✅ Uploaded & Processing started!");
            }

            // Reset form after delay
            setTimeout(() => {
                setShowUploadForm(false);
                setUploadFile(null);
                setUploadProgress("");
                fetchGames();
            }, 2000);

        } catch (err) {
            setUploadProgress(`❌ Error: ${err instanceof Error ? err.message : "Upload failed"}`);
        } finally {
            setUploading(false);
        }
    };

    const handleProcess = async (sourceId: number) => {
        try {
            const res = await fetch(`${API_BASE_URL}/admin/sources/${sourceId}/process`, {
                method: "POST",
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to start processing");
            }

            const data = await res.json();

            // Refresh games to update status
            fetchGames();

            return data.job_id;
        } catch (err) {
            addLog(`Processing trigger failed for source ${sourceId}: ${err instanceof Error ? err.message : "Unknown error"}`);
            return null;
        }
    };

    const [logs, setLogs] = useState<string[]>([]);

    const addLog = (msg: string) => {
        setLogs(prev => [`[${new Date().toISOString().split('T')[1].split('.')[0]}] ${msg}`, ...prev].slice(0, 50));
        console.log(msg); // Also real console
    };

    const handleDebugUrls = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/admin/maintenance/urls`);
            const data = await res.json();
            const msg = data.map((g: any) => `${g.name}: ${g.url}`).join('\n\n');
            addLog(`Debug URLs:\n${msg}`);
        } catch (e) {
            addLog("Failed to fetch URLs");
        }
    };

    const handleFixImages = async () => {
        if (!confirm("RESET images to original Seed Data URLs? (This fixes '400 Bad Request' errors)")) return;
        try {
            const res = await fetch(`${API_BASE_URL}/admin/maintenance/reset-images`, { method: "POST" });
            const data = await res.json();
            addLog(data.message);
            fetchGames();
        } catch (e) {
            addLog("Failed to reset images");
        }
    };

    const handleDeleteSource = async (sourceId: number) => {
        try {
            const res = await fetch(`${API_BASE_URL}/admin/sources/${sourceId}`, { method: "DELETE" });
            if (!res.ok) throw new Error("Failed");
            fetchGames();
        } catch (e) {
            alert("Error deleting source");
        }
    };

    const generateSlug = (name: string) => {
        return name
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, "")
            .replace(/\s+/g, "-")
            .replace(/-+/g, "-")
            .trim();
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-xl text-primary animate-pulse">Loading Arbiter Admin...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground font-sans">
            <div className="max-w-6xl mx-auto p-6">
                {/* Header Section */}
                <div className="flex items-center justify-between mb-8 bg-card p-6 rounded-xl border border-border shadow-sm">
                    <div>
                        <h1 className="text-3xl font-bold text-primary">🎲 Admin Dashboard</h1>
                        <p className="text-muted-foreground mt-1">Manage games and rulebooks</p>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                        <button
                            onClick={async () => {
                                try {
                                    const res = await fetch(`${API_BASE_URL}/admin/maintenance/failed-jobs`);
                                    const data = await res.json();
                                    addLog(`Failed jobs: ${data.failed_count}`);
                                    if (data.jobs && data.jobs.length > 0) {
                                        data.jobs.forEach((job: any) => {
                                            addLog(`❌ Job ${job.job_id}: ${job.exc_info || job.error || 'Unknown error'}`);
                                        });
                                    } else {
                                        addLog(`✅ No failed jobs found`);
                                    }
                                } catch (e) {
                                    addLog(`Error fetching failed jobs: ${e}`);
                                }
                            }}
                            className="px-3 py-2 bg-red-700 hover:bg-red-800 text-white rounded-lg text-sm transition"
                        >
                            🔴 Failed Jobs
                        </button>
                        <button
                            onClick={handleDebugUrls}
                            className="px-3 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg text-sm transition"
                        >
                            📋 Debug URLs
                        </button>
                        <button
                            onClick={handleFixImages}
                            className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm transition"
                        >
                            🔧 Fix Images
                        </button>
                        <button
                            onClick={() => setShowGameForm(true)}
                            className="px-3 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg text-sm transition"
                        >
                            <span>+</span> Add Game
                        </button>
                        <button
                            onClick={() => setShowUploadForm(true)}
                            className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg flex items-center gap-2 transition"
                        >
                            <span>📄</span> Upload PDF
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-destructive/20 border border-destructive text-destructive-foreground p-4 rounded-lg mb-6">
                        {error}
                    </div>
                )}

                {/* Add Game Form */}
                {showGameForm && (
                    <div className="bg-card border border-border rounded-xl p-6 mb-6">
                        <h2 className="text-xl font-semibold mb-4">Add New Game</h2>
                        <form onSubmit={handleCreateGame} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Game Name</label>
                                    <input
                                        type="text"
                                        value={newGame.name}
                                        onChange={(e) => {
                                            setNewGame({
                                                ...newGame,
                                                name: e.target.value,
                                                slug: generateSlug(e.target.value),
                                            });
                                        }}
                                        placeholder="Lord of the Rings: Fate of the Fellowship"
                                        className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Slug</label>
                                    <input
                                        type="text"
                                        value={newGame.slug}
                                        onChange={(e) => setNewGame({ ...newGame, slug: e.target.value })}
                                        placeholder="lotr-fate-of-fellowship"
                                        className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">BGG ID (optional)</label>
                                    <input
                                        type="number"
                                        value={newGame.bgg_id}
                                        onChange={(e) => setNewGame({ ...newGame, bgg_id: e.target.value })}
                                        placeholder="388790"
                                        className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Cover Image URL</label>
                                    <input
                                        type="url"
                                        value={newGame.cover_image_url}
                                        onChange={(e) => setNewGame({ ...newGame, cover_image_url: e.target.value })}
                                        placeholder="https://cf.geekdo-images.com/..."
                                        className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                    />
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    type="submit"
                                    className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90"
                                >
                                    Create Game
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowGameForm(false)}
                                    className="px-6 py-2 bg-muted text-muted-foreground rounded-lg hover:opacity-90"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Upload PDF Form */}
                {showUploadForm && (
                    <div className="bg-card border border-border rounded-xl p-6 mb-6">
                        <h2 className="text-xl font-semibold mb-4">Upload Rulebook PDF</h2>
                        <form onSubmit={handleUpload} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Game</label>
                                    <select
                                        value={uploadData.game_id}
                                        onChange={(e) => setUploadData({ ...uploadData, game_id: e.target.value })}
                                        className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                        required
                                    >
                                        <option value="">Select a game...</option>
                                        {games.map((game) => (
                                            <option key={game.id} value={game.id}>
                                                {game.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Edition</label>
                                    <input
                                        type="text"
                                        value={uploadData.edition}
                                        onChange={(e) => setUploadData({ ...uploadData, edition: e.target.value })}
                                        placeholder="1st Edition"
                                        className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-muted-foreground mb-1">Source Type</label>
                                    <select
                                        value={uploadData.source_type}
                                        onChange={(e) => setUploadData({ ...uploadData, source_type: e.target.value })}
                                        className="w-full px-4 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                                    >
                                        <option value="rulebook">Rulebook</option>
                                        <option value="faq">FAQ</option>
                                        <option value="errata">Errata</option>
                                        <option value="quickstart">Quick Start Guide</option>
                                    </select>
                                </div>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        id="needs_ocr"
                                        checked={uploadData.needs_ocr}
                                        onChange={(e) => setUploadData({ ...uploadData, needs_ocr: e.target.checked })}
                                        className="w-5 h-5 rounded"
                                    />
                                    <label htmlFor="needs_ocr" className="text-sm">
                                        Needs OCR (scanned PDF)
                                    </label>
                                </div>
                            </div>

                            {/* File Drop Zone */}
                            <div
                                className={`border-2 border-dashed rounded-xl p-8 text-center transition ${uploadFile ? "border-primary bg-primary/10" : "border-border hover:border-muted-foreground"
                                    }`}
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={(e) => {
                                    e.preventDefault();
                                    const file = e.dataTransfer.files[0];
                                    if (file?.type === "application/pdf") {
                                        setUploadFile(file);
                                    }
                                }}
                            >
                                {uploadFile ? (
                                    <div>
                                        <p className="text-lg font-medium text-primary">📄 {uploadFile.name}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {(uploadFile.size / (1024 * 1024)).toFixed(2)} MB
                                        </p>
                                        <button
                                            type="button"
                                            onClick={() => setUploadFile(null)}
                                            className="mt-2 text-sm text-destructive hover:underline"
                                        >
                                            Remove
                                        </button>
                                    </div>
                                ) : (
                                    <div>
                                        <p className="text-lg text-muted-foreground">
                                            Drag & drop PDF here, or{" "}
                                            <label className="text-primary cursor-pointer hover:underline">
                                                browse
                                                <input
                                                    type="file"
                                                    accept=".pdf"
                                                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                                                    className="hidden"
                                                />
                                            </label>
                                        </p>
                                        <p className="text-sm text-muted-foreground mt-1">Max 50MB</p>
                                    </div>
                                )}
                            </div>

                            {uploadProgress && (
                                <div className="text-center text-sm py-2">{uploadProgress}</div>
                            )}

                            <div className="flex gap-3">
                                <button
                                    type="submit"
                                    disabled={!uploadFile || uploading}
                                    className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50"
                                >
                                    {uploading ? "Uploading..." : "Upload & Ingest"}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowUploadForm(false);
                                        setUploadFile(null);
                                        setUploadProgress("");
                                    }}
                                    className="px-6 py-2 bg-muted text-muted-foreground rounded-lg hover:opacity-90"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Games List */}
                <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-border">
                        <h2 className="text-xl font-semibold">Games ({games.length})</h2>
                    </div>
                    <div className="divide-y divide-border">
                        {games.map((game) => (
                            <div
                                key={game.id}
                                className="p-4 hover:bg-muted/50 transition cursor-pointer"
                                onClick={() => setSelectedGameId(selectedGameId === game.id ? null : game.id)}
                            >
                                <div className="flex items-center gap-4">
                                    {game.bgg_id && (
                                        <img
                                            src={`${API_BASE_URL}/admin/proxy/image/${game.bgg_id}`}
                                            alt={game.name}
                                            className="w-16 h-16 object-cover rounded-lg bg-muted"
                                            onError={(e) => {
                                                // Hide broken images
                                                (e.target as HTMLImageElement).style.display = 'none';
                                            }}
                                        />
                                    )}
                                    <div className="flex-1">
                                        <h3 className="font-semibold">{game.name}</h3>
                                        <p className="text-sm text-muted-foreground">/{game.slug}</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-muted-foreground">
                                            {game.sources?.length || 0} sources
                                        </div>
                                        {game.bgg_id && (
                                            <a
                                                href={`https://boardgamegeek.com/boardgame/${game.bgg_id}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs text-primary hover:underline"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                BGG #{game.bgg_id}
                                            </a>
                                        )}
                                    </div>
                                </div>

                                {/* Expanded sources view */}
                                {selectedGameId === game.id && game.sources && game.sources.length > 0 && (
                                    <div className="mt-4 pl-20 space-y-2">
                                        {game.sources.map((source) => (
                                            <SourceRow
                                                key={source.id}
                                                source={source}
                                                onProcess={() => handleProcess(source.id)}
                                                onDelete={() => handleDeleteSource(source.id)}
                                                onLog={addLog}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}

                        {games.length === 0 && (
                            <div className="p-8 text-center text-muted-foreground">
                                No games yet. Click &quot;Add Game&quot; to get started.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* System Logs Panel */}
            <div className="fixed bottom-16 left-0 right-0 bg-black/95 text-green-400 text-xs font-mono p-2 h-32 overflow-y-auto border-t border-green-500/30 z-40 shadow-lg">
                <div className="max-w-6xl mx-auto px-6">
                    <div className="flex justify-between items-center mb-1 sticky top-0 bg-black/50 backdrop-blur w-full">
                        <span className="font-bold">SYSTEM LOGS</span>
                        <button onClick={() => setLogs([])} className="text-[10px] text-gray-500 hover:text-white">CLEAR</button>
                    </div>
                    <div className="space-y-0.5">
                        {logs.length === 0 && <div className="text-gray-600 italic">Ready. Logs will appear here...</div>}
                        {logs.map((log, i) => (
                            <div key={i} className="whitespace-pre-wrap font-mono">{log}</div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function SourceRow({ source, onProcess, onDelete, onLog }: { source: Source; onProcess: () => Promise<string | null>; onDelete: () => void; onLog: (msg: string) => void }) {
    const [status, setStatus] = useState<{
        status: string;
        needs_ocr: boolean;
        last_ingested_at: string | null;
    } | null>(null);
    const [jobId, setJobId] = useState<string | null>(null);
    const [progress, setProgress] = useState<number>(0);
    const [progressMessage, setProgressMessage] = useState<string>("");
    const [processing, setProcessing] = useState(false);
    const [deleting, setDeleting] = useState(false);

    // Initial status from props, but careful not to overwrite if processing locally
    useEffect(() => {
        // Only update if we are NOT currently processing a job we know about
        if (!processing) {
            setStatus({
                status: source.last_ingested_at ? "indexed" : source.needs_ocr ? "needs_ocr" : "pending",
                needs_ocr: source.needs_ocr,
                last_ingested_at: source.last_ingested_at,
            });
        }
    }, [source, processing]);

    // Poll Job Status (if we have a job ID)
    useEffect(() => {
        if (!jobId) return;

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/ingest/${jobId}/status`);
                if (res.ok) {
                    const data = await res.json();
                    onLog(`Job ${jobId.substring(0, 8)}... : ${data.state} ${data.pct}% - ${data.message || ''}`);
                    setProgress(data.pct || 0);
                    setProgressMessage(data.message || "");

                    if (data.state === "ready") {
                        onLog(`✅ Job ${jobId.substring(0, 8)}... completed successfully!`);
                        setJobId(null);
                        setProcessing(false);
                        const sourceRes = await fetch(`${API_BASE_URL}/admin/sources/${source.id}/status`);
                        if (sourceRes.ok) {
                            setStatus(await sourceRes.json());
                        }
                    } else if (data.state === "failed") {
                        onLog(`❌ Job ${jobId.substring(0, 8)}... FAILED: ${data.error || data.message || 'Unknown error'}`);
                        setJobId(null);
                        setProcessing(false);
                        const sourceRes = await fetch(`${API_BASE_URL}/admin/sources/${source.id}/status`);
                        if (sourceRes.ok) {
                            setStatus(await sourceRes.json());
                        }
                    }
                } else {
                    onLog(`⚠️ Job poll returned ${res.status}`);
                }
            } catch (e) {
                onLog(`❌ Job poll error: ${e}`);
            }
        }, 2000); // Poll every 2 seconds

        return () => clearInterval(interval);
    }, [jobId, source.id, onLog]);

    // Poll Source Status (fallback) - kept but slower
    useEffect(() => {
        if (jobId || !status || status.status === "indexed") return;
        if (status.status !== "pending" && !processing) return;

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/admin/sources/${source.id}/status`);
                if (res.ok) {
                    const data = await res.json();
                    if (!processing) setStatus(data);

                    if (data.status === "indexed") {
                        setProcessing(false);
                        clearInterval(interval);
                    }
                }
            } catch (e) { }
        }, 5000);
        return () => clearInterval(interval);
    }, [source.id, status, jobId, processing]);

    const handleStartProcess = async () => {
        setProcessing(true);
        onLog(`🚀 Starting ingestion for source ${source.id} (${source.edition})...`);
        try {
            const newJobId = await onProcess();
            if (newJobId) {
                onLog(`📋 Got job ID: ${newJobId}`);
                setJobId(newJobId);
            } else {
                onLog(`❌ No job ID returned - check backend logs`);
                setProcessing(false);
            }
        } catch (e) {
            onLog(`❌ Error starting process: ${e}`);
            setProcessing(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm("Are you sure you want to delete this source?")) return;
        setDeleting(true);
        await onDelete();
        setDeleting(false);
    };

    const displayStatus = () => {
        if (jobId) return (
            <span className="text-blue-500 animate-pulse text-xs font-mono ml-2">
                {progress}% {progressMessage && `- ${progressMessage.substring(0, 20)}...`}
            </span>
        );

        if (processing && !jobId) return <span className="text-blue-500 animate-pulse">🔄 Requesting...</span>;

        if (!status) return <span className="text-muted-foreground">...</span>;

        if (status.status === "indexed") return <span className="text-green-500">✅ Indexed</span>;
        if (status.status === "needs_ocr") return <span className="text-orange-500">📄 Needs OCR</span>;
        if (status.status === "pending") return <span className="text-yellow-500 animate-pulse">⏳ Queued...</span>;
        return <span className="text-muted-foreground">{status.status}</span>;
    };

    return (
        <div className="flex items-center gap-3 text-sm p-2 bg-muted/30 rounded-lg group">
            <span className="text-muted-foreground">📄</span>
            <span className="flex-1 font-medium">
                {source.edition} - {source.source_type}
            </span>

            <div className="flex items-center gap-3">
                {displayStatus()}

                {status?.needs_ocr && !processing && (
                    <span className="text-xs bg-orange-500/20 text-orange-500 px-2 py-0.5 rounded border border-orange-500/30">
                        OCR Required
                    </span>
                )}

                {(!status?.last_ingested_at) && !jobId && (
                    <button
                        onClick={handleStartProcess}
                        disabled={processing || status?.status === "pending"}
                        className="px-3 py-1 bg-primary text-primary-foreground text-xs rounded hover:opacity-90 disabled:opacity-50 transition"
                    >
                        {processing ? "Starting..." : "Process Now"}
                    </button>
                )}

                <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="p-1.5 text-red-500 hover:bg-red-500/10 rounded transition opacity-0 group-hover:opacity-100"
                    title="Delete source"
                >
                    {deleting ? "..." : "🗑️"}
                </button>
            </div>
        </div>
    );
}
