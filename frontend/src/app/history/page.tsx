"use client";

import { Download } from "lucide-react";

export default function HistoryPage() {
    return (
        <div className="min-h-[calc(100vh-5rem)] p-4 sm:p-6 pb-24 sm:pb-8 flex flex-col items-center justify-center">
            <h1 className="text-2xl font-bold tracking-tight mb-4">History</h1>
            <p className="text-muted-foreground text-center max-w-md">
                We are currently upgrading the History tracking system.
                Please check back soon for your past questions!
            </p>
            {/* Minimal logic to satisfy build if needed */}
        </div>
    );
}
