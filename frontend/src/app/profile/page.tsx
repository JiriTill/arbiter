"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { User, Settings, BookOpen, Info, ChevronRight, Monitor, Type, Shield, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    // Initial check (hydration safe)
    useEffect(() => {
        const stored = localStorage.getItem("arbiter_demo_auth");
        if (stored === "true") setIsLoggedIn(true);
    }, []);

    const handleLogin = () => {
        localStorage.setItem("arbiter_demo_auth", "true");
        setIsLoggedIn(true);
    };

    const handleLogout = () => {
        localStorage.removeItem("arbiter_demo_auth");
        setIsLoggedIn(false);
    };

    return (
        <div className="flex flex-col min-h-[calc(100vh-5rem)] p-4 sm:p-6 pb-24">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
                <p className="mt-1 text-muted-foreground">
                    Manage your account and preferences
                </p>
            </div>

            {/* Account Card */}
            <div className="mb-8 rounded-xl border border-border bg-card p-6 flex flex-col sm:flex-row items-center gap-6">
                <div className={cn(
                    "h-20 w-20 rounded-full flex items-center justify-center border",
                    isLoggedIn ? "bg-emerald-500 text-white border-emerald-600" : "bg-muted text-muted-foreground border-border"
                )}>
                    {isLoggedIn ? (
                        <span className="text-2xl font-bold">JD</span>
                    ) : (
                        <User className="h-10 w-10" />
                    )}
                </div>
                <div className="text-center sm:text-left flex-1">
                    <h2 className="text-lg font-semibold flex items-center justify-center sm:justify-start gap-2">
                        {isLoggedIn ? "John Doe" : "Guest User"}
                        {isLoggedIn && <span className="text-[10px] bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded-full border border-amber-500/20">PRO</span>}
                    </h2>
                    <p className="text-sm text-muted-foreground mb-4">
                        {isLoggedIn
                            ? "Member since Jan 2026"
                            : "Sign in to sync your history across devices and upload custom rulebooks."
                        }
                    </p>
                    <div className="flex gap-3 justify-center sm:justify-start">
                        {isLoggedIn ? (
                            <Button variant="outline" onClick={handleLogout} className="text-red-400 hover:text-red-500 hover:bg-red-500/5 mt-auto">
                                Sign Out
                            </Button>
                        ) : (
                            <>
                                <Button onClick={handleLogin} className="bg-emerald-500 hover:bg-emerald-600">
                                    Sign In (Demo)
                                </Button>
                                <Button variant="outline" className="text-muted-foreground">Log In</Button>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="space-y-8">
                {/* Content Section */}
                <section>
                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-1">
                        Content
                    </h3>
                    <div className="rounded-xl border border-border bg-card overflow-hidden divide-y divide-border/50">
                        <MenuItem
                            icon={<BookOpen className="h-5 w-5 text-blue-400" />}
                            label="My Rulebooks"
                            description="Manage personal uploads"
                            href="/profile/rulebooks"
                        />
                        <MenuItem
                            icon={<Shield className="h-5 w-5 text-amber-400" />}
                            label="Saved Verdicts"
                            description="View bookmarked answers"
                            href="/history"
                        />
                    </div>
                </section>

                {/* Preferences Section */}
                <section>
                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-1">
                        Preferences
                    </h3>
                    <div className="rounded-xl border border-border bg-card overflow-hidden divide-y divide-border/50">
                        <div className="p-4 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Monitor className="h-5 w-5 text-purple-400" />
                                <div>
                                    <p className="font-medium">Theme</p>
                                    <p className="text-xs text-muted-foreground">Dark Mode (Default)</p>
                                </div>
                            </div>
                            <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">Locked</span>
                        </div>
                        <div className="p-4 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Type className="h-5 w-5 text-emerald-400" />
                                <div>
                                    <p className="font-medium">Text Size</p>
                                    <p className="text-xs text-muted-foreground">Adjust reading size</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-lg">
                                <button className="w-8 h-8 flex items-center justify-center text-xs font-bold hover:bg-background rounded transition-colors">A</button>
                                <button className="w-8 h-8 flex items-center justify-center text-sm font-bold bg-background shadow rounded text-emerald-500">A</button>
                                <button className="w-8 h-8 flex items-center justify-center text-lg font-bold hover:bg-background rounded transition-colors">A</button>
                            </div>
                        </div>
                    </div>
                </section>

                {/* App Info Section */}
                <section>
                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-1">
                        Application
                    </h3>
                    <div className="rounded-xl border border-border bg-card overflow-hidden divide-y divide-border/50">
                        <MenuItem
                            icon={<Info className="h-5 w-5 text-gray-400" />}
                            label="About The Arbiter"
                            description="Version, AI model, and legal"
                            href="/profile/about"
                        />
                        <div className="p-4 flex items-center gap-3 text-red-400 hover:bg-red-500/5 transition-colors cursor-pointer">
                            <LogOut className="h-5 w-5" />
                            <p className="font-medium">Clear Local Data</p>
                        </div>
                    </div>
                </section>
            </div>

            {/* Version Footer */}
            <div className="mt-12 text-center">
                <p className="text-xs text-muted-foreground">
                    The Arbiter v1.0.0
                    <br />
                    Powered by NeoAntica AI
                </p>
            </div>
        </div>
    );
}

function MenuItem({
    icon,
    label,
    description,
    href
}: {
    icon: React.ReactNode;
    label: string;
    description: string;
    href: string;
}) {
    return (
        <Link href={href}>
            <div className="flex w-full items-center gap-4 p-4 text-left transition-colors hover:bg-muted/30 active:bg-muted/50">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted/50 border border-border/50">
                    {icon}
                </div>
                <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground">{label}</p>
                    <p className="text-sm text-muted-foreground truncate">{description}</p>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground/30" />
            </div>
        </Link>
    );
}
