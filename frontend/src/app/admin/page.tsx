"use client";

import { useState, useEffect, useCallback } from "react";
import {
    BarChart3,
    Users,
    MessageSquare,
    BookOpen,
    Settings,
    Database,
    RefreshCw,
    ThumbsUp,
    ThumbsDown,
    TrendingUp,
    Calendar,
    Image,
    AlertCircle,
    CheckCircle2,
    Loader2
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// Types
// ============================================================================

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

interface DashboardStats {
    total_questions: number;
    total_games: number;
    total_sources: number;
    feedback_helpful: number;
    feedback_negative: number;
    questions_today: number;
    questions_this_week: number;
}

// ============================================================================
// Tab Navigation
// ============================================================================

type TabId = "dashboard" | "games" | "feedback" | "maintenance";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: "dashboard", label: "Dashboard", icon: BarChart3 },
    { id: "games", label: "Games & Sources", icon: BookOpen },
    { id: "feedback", label: "Feedback", icon: MessageSquare },
    { id: "maintenance", label: "Maintenance", icon: Settings },
];

// ============================================================================
// Main Component
// ============================================================================

export default function AdminPage() {
    const [activeTab, setActiveTab] = useState<TabId>("dashboard");
    const [games, setGames] = useState<Game[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [logs, setLogs] = useState<string[]>([]);

    const addLog = useCallback((msg: string) => {
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        setLogs(prev => [`[${timestamp}] ${msg}`, ...prev].slice(0, 100));
        console.log(msg);
    }, []);

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

    const fetchStats = useCallback(async () => {
        try {
            // Fetch multiple endpoints to build stats
            const [historyRes, feedbackRes] = await Promise.all([
                fetch(`${API_BASE_URL}/history?limit=1000`),
                fetch(`${API_BASE_URL}/admin/analytics/feedback-summary`).catch(() => null),
            ]);

            let totalQuestions = 0;
            let questionsToday = 0;
            let questionsThisWeek = 0;

            if (historyRes.ok) {
                const historyData = await historyRes.json();
                totalQuestions = historyData.total || historyData.items?.length || 0;

                // Calculate time-based stats
                const now = new Date();
                const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

                historyData.items?.forEach((item: { created_at: string }) => {
                    const date = new Date(item.created_at);
                    if (date >= today) questionsToday++;
                    if (date >= weekAgo) questionsThisWeek++;
                });
            }

            let feedbackHelpful = 0;
            let feedbackNegative = 0;

            if (feedbackRes?.ok) {
                const feedbackData = await feedbackRes.json();
                feedbackHelpful = feedbackData.helpful || 0;
                feedbackNegative = feedbackData.negative || 0;
            }

            setStats({
                total_questions: totalQuestions,
                total_games: games.length,
                total_sources: games.reduce((acc, g) => acc + (g.sources?.length || 0), 0),
                feedback_helpful: feedbackHelpful,
                feedback_negative: feedbackNegative,
                questions_today: questionsToday,
                questions_this_week: questionsThisWeek,
            });
        } catch (err) {
            console.error("Failed to fetch stats:", err);
        }
    }, [games]);

    useEffect(() => {
        fetchGames();
    }, [fetchGames]);

    useEffect(() => {
        if (games.length > 0) {
            fetchStats();
        }
    }, [games, fetchStats]);

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="flex items-center gap-3 text-xl text-primary">
                    <Loader2 className="h-6 w-6 animate-spin" />
                    Loading Arbiter Admin...
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground">
            {/* Header */}
            <header className="border-b border-border bg-card sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-bold text-lg">
                                A
                            </div>
                            <div>
                                <h1 className="text-xl font-bold">Admin Dashboard</h1>
                                <p className="text-xs text-muted-foreground">The Arbiter Management</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span className="px-2 py-1 bg-emerald-500/10 text-emerald-500 rounded text-xs">
                                Connected
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-6 py-6">
                {/* Tab Navigation */}
                <nav className="flex gap-1 mb-6 bg-muted/50 p-1 rounded-lg w-fit">
                    {TABS.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === tab.id
                                    ? "bg-card text-foreground shadow-sm"
                                    : "text-muted-foreground hover:text-foreground"
                                }`}
                        >
                            <tab.icon className="h-4 w-4" />
                            {tab.label}
                        </button>
                    ))}
                </nav>

                {error && (
                    <div className="bg-destructive/20 border border-destructive text-destructive-foreground p-4 rounded-lg mb-6 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
                        {error}
                    </div>
                )}

                {/* Tab Content */}
                {activeTab === "dashboard" && (
                    <DashboardTab stats={stats} games={games} onRefresh={fetchStats} />
                )}
                {activeTab === "games" && (
                    <GamesTab games={games} onRefresh={fetchGames} addLog={addLog} />
                )}
                {activeTab === "feedback" && (
                    <FeedbackTab addLog={addLog} />
                )}
                {activeTab === "maintenance" && (
                    <MaintenanceTab addLog={addLog} onRefresh={fetchGames} />
                )}
            </div>

            {/* System Logs Panel */}
            <div className="fixed bottom-16 left-0 right-0 bg-black/95 text-green-400 text-xs font-mono p-2 h-32 overflow-y-auto border-t border-green-500/30 z-40">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="flex justify-between items-center mb-1 sticky top-0 bg-black/50 backdrop-blur">
                        <span className="font-bold flex items-center gap-2">
                            <Database className="h-3 w-3" />
                            SYSTEM LOGS
                        </span>
                        <button onClick={() => setLogs([])} className="text-[10px] text-gray-500 hover:text-white">CLEAR</button>
                    </div>
                    <div className="space-y-0.5">
                        {logs.length === 0 && <div className="text-gray-600 italic">Ready. Logs will appear here...</div>}
                        {logs.map((log, i) => (
                            <div key={i} className="whitespace-pre-wrap">{log}</div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Dashboard Tab
// ============================================================================

function DashboardTab({
    stats,
    games,
    onRefresh
}: {
    stats: DashboardStats | null;
    games: Game[];
    onRefresh: () => void;
}) {
    return (
        <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Total Questions"
                    value={stats?.total_questions || 0}
                    icon={MessageSquare}
                    color="emerald"
                    subtitle={`${stats?.questions_today || 0} today`}
                />
                <StatCard
                    title="Games"
                    value={stats?.total_games || 0}
                    icon={BookOpen}
                    color="blue"
                    subtitle={`${stats?.total_sources || 0} sources`}
                />
                <StatCard
                    title="Helpful Feedback"
                    value={stats?.feedback_helpful || 0}
                    icon={ThumbsUp}
                    color="green"
                    subtitle="Positive votes"
                />
                <StatCard
                    title="Negative Feedback"
                    value={stats?.feedback_negative || 0}
                    icon={ThumbsDown}
                    color="red"
                    subtitle="Needs improvement"
                />
            </div>

            {/* Activity Chart Placeholder */}
            <div className="bg-card border border-border rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-emerald-500" />
                        Weekly Activity
                    </h3>
                    <button
                        onClick={onRefresh}
                        className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
                    >
                        <RefreshCw className="h-3 w-3" />
                        Refresh
                    </button>
                </div>
                <div className="h-48 flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                        <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Questions this week: {stats?.questions_this_week || 0}</p>
                        <p className="text-xs mt-1">Chart visualization coming soon</p>
                    </div>
                </div>
            </div>

            {/* Recent Games */}
            <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="font-semibold mb-4">Game Library ({games.length})</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {games.slice(0, 6).map((game) => (
                        <div key={game.id} className="bg-muted/50 rounded-lg p-3 text-center">
                            {game.cover_image_url ? (
                                <img
                                    src={game.cover_image_url}
                                    alt={game.name}
                                    className="w-12 h-12 rounded-lg object-cover mx-auto mb-2"
                                />
                            ) : (
                                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold mx-auto mb-2">
                                    {game.name.charAt(0)}
                                </div>
                            )}
                            <p className="text-xs font-medium truncate">{game.name}</p>
                            <p className="text-xs text-muted-foreground">{game.sources?.length || 0} sources</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function StatCard({
    title,
    value,
    icon: Icon,
    color,
    subtitle
}: {
    title: string;
    value: number;
    icon: React.ElementType;
    color: "emerald" | "blue" | "green" | "red";
    subtitle: string;
}) {
    const colorClasses = {
        emerald: "bg-emerald-500/10 text-emerald-500",
        blue: "bg-blue-500/10 text-blue-500",
        green: "bg-green-500/10 text-green-500",
        red: "bg-red-500/10 text-red-500",
    };

    return (
        <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">{title}</span>
                <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
                    <Icon className="h-4 w-4" />
                </div>
            </div>
            <p className="text-2xl font-bold">{value.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        </div>
    );
}

// ============================================================================
// Games Tab (keeping original functionality)
// ============================================================================

function GamesTab({
    games,
    onRefresh,
    addLog
}: {
    games: Game[];
    onRefresh: () => void;
    addLog: (msg: string) => void;
}) {
    const [showGameForm, setShowGameForm] = useState(false);
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
    const [newGame, setNewGame] = useState({ name: "", slug: "", bgg_id: "", cover_image_url: "" });
    const [uploadData, setUploadData] = useState({ game_id: "", edition: "1st Edition", source_type: "rulebook", needs_ocr: false });
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState("");

    const generateSlug = (name: string) => {
        return name.toLowerCase().replace(/[^a-z0-9\s-]/g, "").replace(/\s+/g, "-").replace(/-+/g, "-").trim();
    };

    const handleCreateGame = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append("name", newGame.name);
            formData.append("slug", newGame.slug);
            if (newGame.bgg_id) formData.append("bgg_id", newGame.bgg_id);
            if (newGame.cover_image_url) formData.append("cover_image_url", newGame.cover_image_url);

            const res = await fetch(`${API_BASE_URL}/admin/games`, { method: "POST", body: formData });
            if (!res.ok) throw new Error((await res.json()).detail || "Failed");

            addLog(`✅ Created game: ${newGame.name}`);
            setShowGameForm(false);
            setNewGame({ name: "", slug: "", bgg_id: "", cover_image_url: "" });
            onRefresh();
        } catch (err) {
            addLog(`❌ Failed to create game: ${err}`);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!uploadFile) return;

        setUploading(true);
        setUploadProgress("Uploading PDF...");

        try {
            const formData = new FormData();
            formData.append("game_id", uploadData.game_id);
            formData.append("edition", uploadData.edition);
            formData.append("source_type", uploadData.source_type);
            formData.append("needs_ocr", String(uploadData.needs_ocr));
            formData.append("file", uploadFile);

            const res = await fetch(`${API_BASE_URL}/admin/sources/upload`, { method: "POST", body: formData });
            if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");

            const result = await res.json();
            addLog(`✅ Uploaded ${uploadFile.name} (${result.file_size_mb} MB)`);
            setUploadProgress("✅ Upload complete!");

            setTimeout(() => {
                setShowUploadForm(false);
                setUploadFile(null);
                setUploadProgress("");
                onRefresh();
            }, 1500);
        } catch (err) {
            addLog(`❌ Upload failed: ${err}`);
            setUploadProgress(`❌ Error: ${err}`);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Actions Bar */}
            <div className="flex gap-2">
                <button
                    onClick={() => setShowGameForm(true)}
                    className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition flex items-center gap-2"
                >
                    + Add Game
                </button>
                <button
                    onClick={() => setShowUploadForm(true)}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition flex items-center gap-2"
                >
                    📄 Upload PDF
                </button>
            </div>

            {/* Add Game Form */}
            {showGameForm && (
                <div className="bg-card border border-border rounded-xl p-6">
                    <h2 className="text-lg font-semibold mb-4">Add New Game</h2>
                    <form onSubmit={handleCreateGame} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-muted-foreground mb-1">Game Name</label>
                                <input
                                    type="text"
                                    value={newGame.name}
                                    onChange={(e) => setNewGame({ ...newGame, name: e.target.value, slug: generateSlug(e.target.value) })}
                                    className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-muted-foreground mb-1">BGG ID</label>
                                <input
                                    type="number"
                                    value={newGame.bgg_id}
                                    onChange={(e) => setNewGame({ ...newGame, bgg_id: e.target.value })}
                                    className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                                    placeholder="e.g., 237182"
                                />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button type="submit" className="px-4 py-2 bg-emerald-500 text-white rounded-lg">Create</button>
                            <button type="button" onClick={() => setShowGameForm(false)} className="px-4 py-2 bg-muted text-muted-foreground rounded-lg">Cancel</button>
                        </div>
                    </form>
                </div>
            )}

            {/* Upload Form */}
            {showUploadForm && (
                <div className="bg-card border border-border rounded-xl p-6">
                    <h2 className="text-lg font-semibold mb-4">Upload Rulebook PDF</h2>
                    <form onSubmit={handleUpload} className="space-y-4">
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm text-muted-foreground mb-1">Game</label>
                                <select
                                    value={uploadData.game_id}
                                    onChange={(e) => setUploadData({ ...uploadData, game_id: e.target.value })}
                                    className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                                    required
                                >
                                    <option value="">Select game...</option>
                                    {games.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-muted-foreground mb-1">Edition</label>
                                <input
                                    type="text"
                                    value={uploadData.edition}
                                    onChange={(e) => setUploadData({ ...uploadData, edition: e.target.value })}
                                    className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-muted-foreground mb-1">Type</label>
                                <select
                                    value={uploadData.source_type}
                                    onChange={(e) => setUploadData({ ...uploadData, source_type: e.target.value })}
                                    className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                                >
                                    <option value="rulebook">Rulebook</option>
                                    <option value="faq">FAQ</option>
                                    <option value="errata">Errata</option>
                                </select>
                            </div>
                        </div>

                        {/* File Drop */}
                        <div
                            className={`border-2 border-dashed rounded-xl p-8 text-center ${uploadFile ? "border-emerald-500 bg-emerald-500/10" : "border-border"}`}
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={(e) => { e.preventDefault(); setUploadFile(e.dataTransfer.files[0]); }}
                        >
                            {uploadFile ? (
                                <div>
                                    <p className="font-medium">📄 {uploadFile.name}</p>
                                    <p className="text-sm text-muted-foreground">{(uploadFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                            ) : (
                                <label className="cursor-pointer">
                                    <p>Drop PDF here or <span className="text-emerald-500">browse</span></p>
                                    <input type="file" accept=".pdf" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} className="hidden" />
                                </label>
                            )}
                        </div>

                        {uploadProgress && <p className="text-center text-sm">{uploadProgress}</p>}

                        <div className="flex gap-2">
                            <button type="submit" disabled={!uploadFile || uploading} className="px-4 py-2 bg-emerald-500 text-white rounded-lg disabled:opacity-50">
                                {uploading ? "Uploading..." : "Upload"}
                            </button>
                            <button type="button" onClick={() => { setShowUploadForm(false); setUploadFile(null); }} className="px-4 py-2 bg-muted text-muted-foreground rounded-lg">Cancel</button>
                        </div>
                    </form>
                </div>
            )}

            {/* Games List */}
            <div className="bg-card border border-border rounded-xl overflow-hidden">
                <div className="p-4 border-b border-border">
                    <h3 className="font-semibold">Games ({games.length})</h3>
                </div>
                <div className="divide-y divide-border">
                    {games.map((game) => (
                        <div key={game.id}>
                            <div
                                className="p-4 hover:bg-muted/50 cursor-pointer flex items-center gap-4"
                                onClick={() => setSelectedGameId(selectedGameId === game.id ? null : game.id)}
                            >
                                {game.cover_image_url ? (
                                    <img src={game.cover_image_url} alt={game.name} className="w-12 h-12 rounded-lg object-cover" />
                                ) : (
                                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold">
                                        {game.name.charAt(0)}
                                    </div>
                                )}
                                <div className="flex-1">
                                    <p className="font-medium">{game.name}</p>
                                    <p className="text-sm text-muted-foreground">/{game.slug}</p>
                                </div>
                                <div className="text-right text-sm text-muted-foreground">
                                    <p>{game.sources?.length || 0} sources</p>
                                    {game.bgg_id && <p className="text-xs">BGG #{game.bgg_id}</p>}
                                </div>
                            </div>
                            {selectedGameId === game.id && game.sources && (
                                <div className="pl-20 pb-4 space-y-2">
                                    {game.sources.map((s) => (
                                        <div key={s.id} className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg text-sm">
                                            <span>📄</span>
                                            <span className="flex-1">{s.edition} - {s.source_type}</span>
                                            <span className={s.last_ingested_at ? "text-green-500" : "text-yellow-500"}>
                                                {s.last_ingested_at ? "✅ Indexed" : "⏳ Pending"}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Feedback Tab
// ============================================================================

function FeedbackTab({ addLog }: { addLog: (msg: string) => void }) {
    const [feedback, setFeedback] = useState<Array<{
        id: number;
        feedback_type: string;
        user_note: string | null;
        created_at: string;
        question?: string;
    }>>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const res = await fetch(`${API_BASE_URL}/admin/analytics/feedback`);
                if (res.ok) {
                    const data = await res.json();
                    setFeedback(data.items || []);
                }
            } catch (e) {
                addLog(`Failed to fetch feedback: ${e}`);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [addLog]);

    const stats = {
        helpful: feedback.filter(f => f.feedback_type === "helpful").length,
        wrong_quote: feedback.filter(f => f.feedback_type === "wrong_quote").length,
        wrong_interpretation: feedback.filter(f => f.feedback_type === "wrong_interpretation").length,
        other: feedback.filter(f => !["helpful", "wrong_quote", "wrong_interpretation"].includes(f.feedback_type)).length,
    };

    if (loading) {
        return <div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin" /></div>;
    }

    return (
        <div className="space-y-6">
            {/* Feedback Stats */}
            <div className="grid grid-cols-4 gap-4">
                <div className="bg-card border border-border rounded-xl p-4 text-center">
                    <ThumbsUp className="h-6 w-6 text-green-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold">{stats.helpful}</p>
                    <p className="text-sm text-muted-foreground">Helpful</p>
                </div>
                <div className="bg-card border border-border rounded-xl p-4 text-center">
                    <AlertCircle className="h-6 w-6 text-red-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold">{stats.wrong_quote}</p>
                    <p className="text-sm text-muted-foreground">Wrong Quote</p>
                </div>
                <div className="bg-card border border-border rounded-xl p-4 text-center">
                    <AlertCircle className="h-6 w-6 text-orange-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold">{stats.wrong_interpretation}</p>
                    <p className="text-sm text-muted-foreground">Wrong Interpretation</p>
                </div>
                <div className="bg-card border border-border rounded-xl p-4 text-center">
                    <MessageSquare className="h-6 w-6 text-blue-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold">{stats.other}</p>
                    <p className="text-sm text-muted-foreground">Other</p>
                </div>
            </div>

            {/* Feedback List */}
            <div className="bg-card border border-border rounded-xl overflow-hidden">
                <div className="p-4 border-b border-border">
                    <h3 className="font-semibold">Recent Feedback ({feedback.length})</h3>
                </div>
                <div className="divide-y divide-border max-h-96 overflow-y-auto">
                    {feedback.length === 0 ? (
                        <div className="p-8 text-center text-muted-foreground">
                            No feedback received yet
                        </div>
                    ) : (
                        feedback.slice(0, 50).map((f) => (
                            <div key={f.id} className="p-4">
                                <div className="flex items-center gap-2 mb-1">
                                    {f.feedback_type === "helpful" ? (
                                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    ) : (
                                        <AlertCircle className="h-4 w-4 text-red-500" />
                                    )}
                                    <span className="text-sm font-medium capitalize">{f.feedback_type.replace("_", " ")}</span>
                                    <span className="text-xs text-muted-foreground ml-auto">
                                        {new Date(f.created_at).toLocaleString()}
                                    </span>
                                </div>
                                {f.user_note && (
                                    <p className="text-sm text-muted-foreground ml-6">{f.user_note}</p>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Maintenance Tab
// ============================================================================

function MaintenanceTab({
    addLog,
    onRefresh
}: {
    addLog: (msg: string) => void;
    onRefresh: () => void;
}) {
    const [syncing, setSyncing] = useState(false);

    const handleSyncImages = async () => {
        setSyncing(true);
        addLog("🔄 Syncing game images from BGG...");
        try {
            const res = await fetch(`${API_BASE_URL}/admin/maintenance/sync-bgg-images`, { method: "POST" });
            const data = await res.json();
            addLog(`✅ Synced ${data.updated} games with BGG images`);
            if (data.errors > 0) {
                addLog(`⚠️ ${data.errors} games had errors`);
                data.error_details?.forEach((e: { game: string; error: string }) => {
                    addLog(`   - ${e.game}: ${e.error}`);
                });
            }
            onRefresh();
        } catch (e) {
            addLog(`❌ Sync failed: ${e}`);
        } finally {
            setSyncing(false);
        }
    };

    const handleCheckOCR = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/admin/maintenance/ocr-status`);
            const data = await res.json();
            if (data.ocr_available) {
                addLog(`✅ Cloud OCR: AVAILABLE`);
            } else {
                addLog(`❌ Cloud OCR: NOT AVAILABLE - ${data.details?.error || 'Unknown'}`);
            }
        } catch (e) {
            addLog(`❌ OCR check failed: ${e}`);
        }
    };

    const handleCheckFailedJobs = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/admin/maintenance/failed-jobs`);
            const data = await res.json();
            addLog(`📋 Failed jobs: ${data.failed_count}`);
            data.jobs?.forEach((job: { job_id: string; exc_info?: string }) => {
                addLog(`   ❌ ${job.job_id}: ${job.exc_info?.substring(0, 100) || 'Unknown error'}`);
            });
        } catch (e) {
            addLog(`❌ Failed to check jobs: ${e}`);
        }
    };

    return (
        <div className="space-y-6">
            {/* Maintenance Actions */}
            <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="font-semibold mb-4">Maintenance Actions</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <button
                        onClick={handleSyncImages}
                        disabled={syncing}
                        className="p-4 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-xl text-center transition disabled:opacity-50"
                    >
                        {syncing ? <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" /> : <Image className="h-6 w-6 text-emerald-500 mx-auto mb-2" />}
                        <p className="text-sm font-medium">Sync BGG Images</p>
                        <p className="text-xs text-muted-foreground">Fetch from BoardGameGeek</p>
                    </button>

                    <button
                        onClick={handleCheckOCR}
                        className="p-4 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-xl text-center transition"
                    >
                        <Database className="h-6 w-6 text-purple-500 mx-auto mb-2" />
                        <p className="text-sm font-medium">Check OCR Status</p>
                        <p className="text-xs text-muted-foreground">Verify cloud OCR</p>
                    </button>

                    <button
                        onClick={handleCheckFailedJobs}
                        className="p-4 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-xl text-center transition"
                    >
                        <AlertCircle className="h-6 w-6 text-red-500 mx-auto mb-2" />
                        <p className="text-sm font-medium">Failed Jobs</p>
                        <p className="text-xs text-muted-foreground">View processing errors</p>
                    </button>

                    <button
                        onClick={onRefresh}
                        className="p-4 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 rounded-xl text-center transition"
                    >
                        <RefreshCw className="h-6 w-6 text-blue-500 mx-auto mb-2" />
                        <p className="text-sm font-medium">Refresh Data</p>
                        <p className="text-xs text-muted-foreground">Reload all games</p>
                    </button>
                </div>
            </div>

            {/* System Info */}
            <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="font-semibold mb-4">System Information</h3>
                <div className="space-y-2 text-sm">
                    <div className="flex justify-between py-2 border-b border-border">
                        <span className="text-muted-foreground">Backend API</span>
                        <span className="font-mono">{API_BASE_URL}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b border-border">
                        <span className="text-muted-foreground">Frontend</span>
                        <span className="font-mono">arbiter-sage.vercel.app</span>
                    </div>
                    <div className="flex justify-between py-2">
                        <span className="text-muted-foreground">Database</span>
                        <span className="font-mono">Supabase PostgreSQL</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
