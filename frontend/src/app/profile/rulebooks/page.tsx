"use client";

import Link from "next/link";
import { ArrowLeft, Upload, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function RulebooksPage() {
    return (
        <div className="flex flex-col min-h-[calc(100vh-5rem)] p-4 sm:p-6 pb-24 max-w-2xl mx-auto">
            <div className="mb-6">
                <Link href="/profile">
                    <Button variant="ghost" size="sm" className="pl-0 gap-2 text-muted-foreground hover:text-foreground">
                        <ArrowLeft className="h-4 w-4" />
                        Back to Profile
                    </Button>
                </Link>
            </div>

            <div className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight">My Rulebooks</h1>
                <p className="mt-1 text-muted-foreground">
                    Manage your custom rulebook collection
                </p>
            </div>

            {/* Empty State */}
            <div className="flex flex-col items-center justify-center py-16 text-center border-2 border-dashed border-border rounded-xl bg-muted/10">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h2 className="text-lg font-semibold mb-2">No rulebooks uploaded</h2>
                <p className="text-muted-foreground max-w-sm mb-6">
                    You can upload your own PDF rulebooks to search through them with the Arbiter AI.
                </p>
                <div className="flex flex-col gap-3 w-full max-w-xs">
                    <Button className="w-full gap-2" disabled>
                        <Upload className="h-4 w-4" />
                        Upload PDF (Pro)
                    </Button>
                    <p className="text-xs text-muted-foreground">
                        Custom uploads are available for Pro subscribers.
                    </p>
                </div>
            </div>

            {/* Request */}
            <div className="mt-12">
                <h3 className="font-semibold mb-4">Missing a popular game?</h3>
                <div className="bg-card border border-border rounded-xl p-6">
                    <p className="text-sm text-muted-foreground mb-4">
                        We are constantly adding new games to the public library. Let us know what we should add next.
                    </p>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Game Name (e.g. Frosthaven)"
                            className="flex-1 h-10 px-3 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                        />
                        <Button variant="secondary">Request</Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
