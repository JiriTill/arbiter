"use client";

import { User, Settings, BookOpen, Info } from "lucide-react";

export default function ProfilePage() {
    return (
        <div className="flex flex-col px-4 py-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
                <p className="mt-1 text-muted-foreground">
                    Manage your account and preferences
                </p>
            </div>

            {/* Profile Card */}
            <div className="mb-6 flex items-center gap-4 rounded-lg border border-border bg-card p-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                    <User className="h-8 w-8 text-muted-foreground" />
                </div>
                <div>
                    <p className="font-medium">Guest User</p>
                    <p className="text-sm text-muted-foreground">Sign in to save your history</p>
                </div>
            </div>

            {/* Menu Items */}
            <div className="space-y-2">
                <MenuItem
                    icon={<BookOpen className="h-5 w-5" />}
                    label="My Rulebooks"
                    description="Manage uploaded rulebooks"
                />
                <MenuItem
                    icon={<Settings className="h-5 w-5" />}
                    label="Preferences"
                    description="App settings and display"
                />
                <MenuItem
                    icon={<Info className="h-5 w-5" />}
                    label="About"
                    description="Version and legal info"
                />
            </div>

            {/* Version Info */}
            <div className="mt-auto pt-8 text-center">
                <p className="text-xs text-muted-foreground">
                    The Arbiter v0.1.0
                </p>
            </div>
        </div>
    );
}

function MenuItem({
    icon,
    label,
    description,
}: {
    icon: React.ReactNode;
    label: string;
    description: string;
}) {
    return (
        <button
            type="button"
            className="flex w-full items-center gap-4 rounded-lg border border-border bg-card p-4 text-left transition-colors hover:bg-card/80"
        >
            <div className="text-muted-foreground">{icon}</div>
            <div className="flex-1">
                <p className="font-medium">{label}</p>
                <p className="text-sm text-muted-foreground">{description}</p>
            </div>
        </button>
    );
}
