"use client";

import Link from "next/link";
import { ArrowLeft, Brain, Shield, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AboutPage() {
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

            <div className="space-y-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">About The Arbiter</h1>
                    <p className="text-lg text-muted-foreground">
                        The world's most accurate board game rules companion.
                    </p>
                </div>

                <div className="prose prose-invert max-w-none">
                    <p>
                        The Arbiter is an AI-powered assistant designed to settle board game disputes instantly.
                        Unlike generic chatbots, The Arbiter reads specific versions of official rulebooks to provide answers backed by evidence.
                    </p>
                </div>

                <div className="grid gap-6 sm:grid-cols-2">
                    <Feature
                        icon={<Shield className="h-6 w-6 text-emerald-400" />}
                        title="Verifiable Truth"
                        description="We don't hallucinate. Every answer is grounded in an actual sentence from the rulebook."
                    />
                    <Feature
                        icon={<Brain className="h-6 w-6 text-purple-400" />}
                        title="Context Aware"
                        description="We understand specific game editions, expansions, and common house rule conflicts."
                    />
                    <Feature
                        icon={<Zap className="h-6 w-6 text-amber-400" />}
                        title="Lightning Fast"
                        description="Get answers in seconds so you can get back to playing."
                    />
                </div>

                <div className="bg-muted/30 rounded-xl p-6 border border-border">
                    <h3 className="font-semibold mb-2">How it works</h3>
                    <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                        <li>You ask a question in natural language.</li>
                        <li>We search our indexed vector database of rulebooks.</li>
                        <li>Our AI analyzes the relevant text chunks.</li>
                        <li>We formulate a verdict and verify it against the text.</li>
                    </ol>
                </div>

                <div className="pt-8 text-center text-xs text-muted-foreground">
                    <p>© 2026 NeoAntica. All rights reserved.</p>
                </div>
            </div>
        </div>
    );
}

function Feature({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
    return (
        <div className="flex flex-col gap-2 p-4 rounded-xl bg-card border border-border">
            <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center mb-1">
                {icon}
            </div>
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
        </div>
    );
}
