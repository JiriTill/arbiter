"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, CheckCircle2, Zap, Shield, MessageCircleQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";

// How it works steps
const steps = [
    {
        icon: <MessageCircleQuestion className="h-8 w-8" />,
        title: "Ask Your Question",
        description: "Type any rules question about your board game",
    },
    {
        icon: <BookOpen className="h-8 w-8" />,
        title: "AI Searches Rulebooks",
        description: "The Arbiter scans official rulebooks instantly",
    },
    {
        icon: <CheckCircle2 className="h-8 w-8" />,
        title: "Get Verified Answer",
        description: "Receive an answer with exact page citations",
    },
];

// Features
const features = [
    {
        icon: <Zap className="h-6 w-6 text-amber-400" />,
        title: "Instant Answers",
        description: "No more flipping through rulebooks",
    },
    {
        icon: <Shield className="h-6 w-6 text-emerald-400" />,
        title: "Verified Citations",
        description: "Every answer includes page references",
    },
    {
        icon: <BookOpen className="h-6 w-6 text-blue-400" />,
        title: "Official Sources",
        description: "Answers from official rulebooks only",
    },
];

// Popular games (visual showcase)
const featuredGames = [
    { name: "Catan", initial: "C", color: "from-orange-500 to-red-600" },
    { name: "Root", initial: "R", color: "from-green-500 to-emerald-600" },
    { name: "Wingspan", initial: "W", color: "from-sky-500 to-blue-600" },
    { name: "Lord of the Rings", initial: "L", color: "from-amber-500 to-yellow-600" },
];

export default function LandingPage() {
    return (
        <div className="min-h-screen flex flex-col">
            {/* Hero Section */}
            <section className="relative flex-1 flex flex-col items-center justify-center px-6 py-16 text-center overflow-hidden">
                {/* Background gradient */}
                <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-background to-background pointer-events-none" />

                {/* Gavel Icon - Logo placeholder */}
                <div className="relative mb-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-2xl shadow-emerald-500/20">
                        <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="h-10 w-10 text-white"
                        >
                            {/* Gavel icon */}
                            <path d="M14.5 12.5L6 21l-3-3 8.5-8.5" />
                            <path d="M18.5 8.5L21 6l-3-3-2.5 2.5" />
                            <path d="M12 10l4-4" />
                            <rect x="12" y="6" width="6" height="4" rx="1" transform="rotate(45 15 8)" />
                        </svg>
                    </div>
                </div>

                {/* Main Headline */}
                <h1 className="relative text-4xl sm:text-5xl font-bold tracking-tight mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
                    <span className="bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
                        The Arbiter
                    </span>
                </h1>

                {/* Tagline */}
                <p className="relative text-lg sm:text-xl text-muted-foreground max-w-md mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-200">
                    Instant, verified answers to your board game rules questions
                </p>

                {/* CTA Button */}
                <Link href="/ask" className="relative animate-in fade-in slide-in-from-bottom-4 duration-500 delay-300">
                    <Button
                        size="lg"
                        className="h-14 px-8 text-lg font-semibold bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/25 transition-all hover:shadow-xl hover:shadow-emerald-500/30"
                    >
                        Ask a Question
                        <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                </Link>

                {/* Trust indicator */}
                <p className="relative mt-6 text-sm text-muted-foreground animate-in fade-in duration-500 delay-500">
                    <CheckCircle2 className="inline h-4 w-4 mr-1 text-emerald-500" />
                    Every answer verified against official rulebooks
                </p>
            </section>

            {/* How It Works */}
            <section className="px-6 py-12 bg-card/30">
                <h2 className="text-center text-xl font-semibold mb-8 text-muted-foreground">
                    How It Works
                </h2>
                <div className="max-w-lg mx-auto space-y-6">
                    {steps.map((step, idx) => (
                        <div
                            key={idx}
                            className="flex items-start gap-4 animate-in fade-in slide-in-from-left-4 duration-300"
                            style={{ animationDelay: `${idx * 100}ms` }}
                        >
                            <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                                {step.icon}
                            </div>
                            <div>
                                <h3 className="font-semibold mb-1">{step.title}</h3>
                                <p className="text-sm text-muted-foreground">{step.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Features */}
            <section className="px-6 py-12">
                <div className="max-w-lg mx-auto grid grid-cols-1 gap-4">
                    {features.map((feature, idx) => (
                        <div
                            key={idx}
                            className="flex items-center gap-3 p-4 rounded-xl bg-card/50 border border-border/50"
                        >
                            <div className="flex-shrink-0">{feature.icon}</div>
                            <div>
                                <h3 className="font-medium text-sm">{feature.title}</h3>
                                <p className="text-xs text-muted-foreground">{feature.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Supported Games Preview */}
            <section className="px-6 py-12 bg-card/30">
                <h2 className="text-center text-xl font-semibold mb-6">
                    Games We Support
                </h2>
                <div className="flex justify-center gap-4 flex-wrap max-w-lg mx-auto">
                    {featuredGames.map((game, idx) => (
                        <div
                            key={idx}
                            className="flex flex-col items-center gap-2"
                        >
                            <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${game.color} flex items-center justify-center text-2xl font-bold text-white shadow-lg`}>
                                {game.initial}
                            </div>
                            <span className="text-xs text-muted-foreground">{game.name}</span>
                        </div>
                    ))}
                </div>
                <p className="text-center text-sm text-muted-foreground mt-6">
                    + we&apos;re adding more games every week!
                </p>
            </section>

            {/* Final CTA */}
            <section className="px-6 py-16 text-center">
                <h2 className="text-2xl font-bold mb-4">Ready to Settle the Debate?</h2>
                <p className="text-muted-foreground mb-6">
                    Stop arguing, start playing.
                </p>
                <Link href="/ask">
                    <Button
                        size="lg"
                        className="bg-emerald-500 hover:bg-emerald-600 text-white"
                    >
                        Ask The Arbiter Now
                        <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                </Link>
            </section>

            {/* Spacer for bottom nav */}
            <div className="h-20" />
        </div>
    );
}
