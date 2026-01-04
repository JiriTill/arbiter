"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { ArrowRight, BookOpen, CheckCircle2, Zap, Shield, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VerdictShowcase } from "@/components/landing/VerdictShowcase";
import { cn } from "@/lib/utils";

// Typing effect hook
function useTypewriter(phrases: string[], speed = 50, pause = 3000) {
    const [index, setIndex] = useState(0);
    const [subIndex, setSubIndex] = useState(0);
    const [reverse, setReverse] = useState(false);
    const [blink, setBlink] = useState(true);

    // Blinking cursor
    useEffect(() => {
        const timeout = setInterval(() => {
            setBlink((prev) => !prev);
        }, 500);
        return () => clearInterval(timeout);
    }, []);

    // Typing logic
    useEffect(() => {
        if (subIndex === phrases[index].length + 1 && !reverse) {
            const timeout = setTimeout(() => {
                setReverse(true);
            }, pause);
            return () => clearTimeout(timeout);
        }

        if (subIndex === 0 && reverse) {
            setReverse(false);
            setIndex((prev) => (prev + 1) % phrases.length);
            return;
        }

        const timeout = setTimeout(() => {
            setSubIndex((prev) => prev + (reverse ? -1 : 1));
        }, Math.max(reverse ? speed / 2 : speed, parseInt(Math.random() * 50 + "")));

        return () => clearTimeout(timeout);
    }, [subIndex, index, reverse, phrases, speed, pause]);

    return `${phrases[index].substring(0, subIndex)}${blink ? "|" : " "}`;
}

const steps = [
    {
        icon: <Search className="h-6 w-6" />,
        title: "Ask a Question",
        description: "Type any rules dispute in plain English",
    },
    {
        icon: <BookOpen className="h-6 w-6" />,
        title: "AI Scans Rulebooks",
        description: "We verify against official PDFs instantly",
    },
    {
        icon: <CheckCircle2 className="h-6 w-6" />,
        title: "Get Verified Verdict",
        description: "Receive a clear Yes/No with citations",
    },
];

const featuredGames = [
    { name: "Catan", initial: "Ca", color: "from-orange-500 to-red-600", players: "3-4" },
    { name: "Root", initial: "Ro", color: "from-emerald-600 to-green-700", players: "2-4" },
    { name: "Wingspan", initial: "Wi", color: "from-sky-400 to-blue-500", players: "1-5" },
    { name: "Scythe", initial: "Sc", color: "from-red-700 to-red-900", players: "1-5" },
    { name: "Azul", initial: "Az", color: "from-blue-500 to-indigo-600", players: "2-4" },
    { name: "Dune Imp.", initial: "Du", color: "from-amber-600 to-orange-700", players: "1-4" },
];

export default function LandingPage() {
    const typedText = useTypewriter([
        "Can I play a Knight before rolling dice?",
        "Does the robber block production for everyone?",
        "Can I trade with the bank at 3:1?",
        "Do eggs count as points in Wingspan?",
    ]);

    return (
        <div className="min-h-screen flex flex-col overflow-x-hidden">
            {/* Hero Section */}
            <section className="relative flex flex-col items-center justify-center px-4 pt-16 pb-20 text-center">
                {/* Background effects */}
                <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 via-background to-background pointer-events-none" />
                <div className="absolute top-20 left-10 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none opacity-50 animate-pulse" />
                <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none opacity-30" />

                {/* Main Headline */}
                <div className="relative z-10 space-y-4 max-w-4xl mx-auto">
                    <div className="flex items-center justify-center gap-2 mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
                            v1.0 Now Live
                        </span>
                    </div>

                    <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight animate-in fade-in slide-in-from-bottom-8 duration-700 delay-100">
                        The Arbiter
                    </h1>

                    <p className="text-xl sm:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
                        Stop arguing. Start playing.
                        <br />
                        <span className="text-foreground/90 font-medium">Instant, verified answers</span> to your board game rules questions.
                    </p>

                    {/* Typing Search Sim */}
                    <div className="mt-10 mx-auto max-w-xl w-full animate-in fade-in zoom-in-95 duration-700 delay-300">
                        <div className="relative group">
                            <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-200"></div>
                            <div className="relative bg-card border border-border rounded-xl p-4 flex items-center shadow-2xl">
                                <Search className="h-6 w-6 text-muted-foreground mr-4" />
                                <div className="text-lg text-muted-foreground font-mono truncate w-full text-left">
                                    {typedText}
                                </div>
                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                    <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-white">
                                        Ask
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* CTA */}
                    <div className="mt-10 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500">
                        <Link href="/ask">
                            <Button
                                size="lg"
                                className="h-14 px-10 text-lg font-bold bg-emerald-500 hover:bg-emerald-600 text-white shadow-xl shadow-emerald-500/20 hover:shadow-emerald-500/30 hover:scale-105 transition-all"
                            >
                                Try it now
                                <ArrowRight className="ml-2 h-5 w-5" />
                            </Button>
                        </Link>
                        <p className="mt-4 text-sm text-muted-foreground">
                            No account required • 100% Free
                        </p>
                    </div>
                </div>
            </section>

            {/* Verdict Showcase - NEW */}
            <section className="py-20 px-4 bg-muted/30 border-y border-border/50">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold mb-4">See it in action</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                            The Arbiter doesn't just guess. It reads specific rulebooks and gives you a definitive YES or NO with evidence.
                        </p>
                    </div>

                    <VerdictShowcase />

                    <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                        {steps.map((step, idx) => (
                            <div key={idx} className="flex flex-col items-center text-center space-y-3 p-6 rounded-2xl bg-card border border-border/50 hover:border-emerald-500/30 transition-colors">
                                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500 mb-2">
                                    {step.icon}
                                </div>
                                <h3 className="font-semibold text-lg">{step.title}</h3>
                                <p className="text-muted-foreground">{step.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Supported Games */}
            <section className="py-20 px-4">
                <div className="max-w-6xl mx-auto text-center">
                    <h2 className="text-3xl font-bold mb-10">Supported Games</h2>

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-6">
                        {featuredGames.map((game, idx) => (
                            <div key={idx} className="group relative aspect-square">
                                <div className={cn(
                                    "absolute inset-0 rounded-2xl bg-gradient-to-br opacity-80 transition-all duration-300 group-hover:scale-105 group-hover:opacity-100 shadow-lg",
                                    game.color
                                )} />
                                <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-2">
                                    <span className="text-3xl font-bold mb-1 drop-shadow-md">{game.initial}</span>
                                    <span className="font-semibold text-sm drop-shadow-md">{game.name}</span>
                                    <span className="text-[10px] opacity-80 mt-1">{game.players} Players</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-12 p-8 rounded-3xl bg-card border border-border max-w-3xl mx-auto text-center relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500 to-transparent" />
                        <h3 className="text-2xl font-bold mb-2">Don't see your game?</h3>
                        <p className="text-muted-foreground mb-6">
                            We are indexing new rulebooks every week. Check back soon or request a game.
                        </p>
                        <Link href="/ask">
                            <Button variant="outline" className="border-border hover:bg-muted">
                                Browse All Games
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-6 border-t border-border mt-auto">
                <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-bold">A</div>
                        <span className="font-bold">The Arbiter</span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                        © 2026 NeoAntica. built with ❤️ for board gamers.
                    </div>
                </div>
            </footer>
        </div>
    );
}
