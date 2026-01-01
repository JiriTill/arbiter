"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
    id: string;
    message: string;
    type: ToastType;
    duration?: number;
}

interface ToastContextValue {
    toasts: Toast[];
    addToast: (message: string, type?: ToastType, duration?: number) => void;
    removeToast: (id: string) => void;
}

// Global toast state (simple implementation)
let toastListeners: ((toasts: Toast[]) => void)[] = [];
let currentToasts: Toast[] = [];

function notifyListeners() {
    toastListeners.forEach(listener => listener([...currentToasts]));
}

export function addToast(message: string, type: ToastType = "info", duration = 5000) {
    const id = Math.random().toString(36).substring(7);
    const toast: Toast = { id, message, type, duration };

    currentToasts = [...currentToasts, toast];
    notifyListeners();

    if (duration > 0) {
        setTimeout(() => removeToast(id), duration);
    }

    return id;
}

export function removeToast(id: string) {
    currentToasts = currentToasts.filter(t => t.id !== id);
    notifyListeners();
}

// Convenience methods
export const toast = {
    success: (message: string, duration?: number) => addToast(message, "success", duration),
    error: (message: string, duration?: number) => addToast(message, "error", duration ?? 8000),
    warning: (message: string, duration?: number) => addToast(message, "warning", duration),
    info: (message: string, duration?: number) => addToast(message, "info", duration),
};

const iconMap = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
};

const colorMap = {
    success: "bg-green-500/10 border-green-500/30 text-green-400",
    error: "bg-red-500/10 border-red-500/30 text-red-400",
    warning: "bg-amber-500/10 border-amber-500/30 text-amber-400",
    info: "bg-blue-500/10 border-blue-500/30 text-blue-400",
};

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
    const Icon = iconMap[toast.type];

    return (
        <div
            className={cn(
                "flex items-start gap-3 rounded-lg border p-4 shadow-lg backdrop-blur-sm",
                "animate-in slide-in-from-right-5 fade-in duration-300",
                colorMap[toast.type]
            )}
            role="alert"
        >
            <Icon className="h-5 w-5 shrink-0 mt-0.5" />
            <p className="flex-1 text-sm font-medium text-foreground">
                {toast.message}
            </p>
            <button
                onClick={onRemove}
                className="shrink-0 rounded-md p-1 hover:bg-white/10 transition-colors"
                aria-label="Dismiss"
            >
                <X className="h-4 w-4" />
            </button>
        </div>
    );
}

/**
 * Toast container component. Add this to your layout once.
 */
export function ToastContainer() {
    const [toasts, setToasts] = useState<Toast[]>([]);

    useEffect(() => {
        const listener = (newToasts: Toast[]) => setToasts(newToasts);
        toastListeners.push(listener);

        // Sync initial state
        setToasts([...currentToasts]);

        return () => {
            toastListeners = toastListeners.filter(l => l !== listener);
        };
    }, []);

    if (toasts.length === 0) return null;

    return (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
            {toasts.map(t => (
                <div key={t.id} className="pointer-events-auto">
                    <ToastItem toast={t} onRemove={() => removeToast(t.id)} />
                </div>
            ))}
        </div>
    );
}
