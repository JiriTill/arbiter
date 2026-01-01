"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import {
    VerdictCard,
    QuoteCard,
    CitationCard,
    SupersededCard,
} from "@/components/arbiter";

// Demo data for showcasing the components
const DEMO_DATA = {
    verdict: "Yes, you can trade with the bank at a 2:1 ratio if you have the matching port.",
    confidence: "high" as const,
    quote: "A player who has built a settlement at a harbor can trade with the bank at a more favorable rate. A 2:1 harbor allows the player to trade 2 resource cards of the type shown for any 1 other resource card.",
    page: 12,
    verified: true,
    citation: {
        sourceType: "rulebook" as const,
        edition: "Catan 5th Edition (2015)",
        sourceUrl: "https://example.com/catan-rules.pdf",
        page: 12,
    },
    superseded: {
        oldQuote: "Trading with the bank always requires 4 identical resource cards for 1 resource card of your choice.",
        oldPage: 8,
        reason: "The base trading rule on page 8 is modified by the harbor rules on page 12. Players with harbor settlements get improved trading rates.",
    },
};

export default function ComponentsDemoPage() {
    return (
        <div className="min-h-screen p-4 sm:p-6">
            {/* Header */}
            <div className="mb-6 flex items-center gap-3">
                <Link
                    href="/ask"
                    className="flex h-10 w-10 items-center justify-center rounded-lg border border-border hover:bg-muted"
                >
                    <ArrowLeft className="h-5 w-5" />
                </Link>
                <div>
                    <h1 className="text-xl font-bold">Component Demo</h1>
                    <p className="text-sm text-muted-foreground">
                        Answer card components preview
                    </p>
                </div>
            </div>

            {/* Card Stack Demo */}
            <div className="mx-auto max-w-2xl space-y-4">
                {/* Question Context */}
                <div className="rounded-lg border border-dashed border-border bg-card/30 p-4 text-center">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Question</p>
                    <p className="font-medium">"Can I trade with the bank at 2:1 if I have a harbor?"</p>
                    <p className="text-xs text-muted-foreground mt-1">Catan • 5th Edition</p>
                </div>

                {/* Verdict Card - High Confidence */}
                <VerdictCard
                    verdict={DEMO_DATA.verdict}
                    confidence={DEMO_DATA.confidence}
                />

                {/* Quote Card - Verified */}
                <QuoteCard
                    quote={DEMO_DATA.quote}
                    page={DEMO_DATA.page}
                    verified={DEMO_DATA.verified}
                />

                {/* Citation Card */}
                <CitationCard
                    sourceType={DEMO_DATA.citation.sourceType}
                    edition={DEMO_DATA.citation.edition}
                    sourceUrl={DEMO_DATA.citation.sourceUrl}
                    page={DEMO_DATA.citation.page}
                />

                {/* Superseded Card */}
                <SupersededCard
                    oldQuote={DEMO_DATA.superseded.oldQuote}
                    oldPage={DEMO_DATA.superseded.oldPage}
                    reason={DEMO_DATA.superseded.reason}
                />

                {/* Divider */}
                <div className="my-8 border-t border-border" />

                {/* Additional Examples */}
                <h2 className="text-lg font-semibold">More Examples</h2>

                {/* Medium Confidence */}
                <VerdictCard
                    verdict="The rules are ambiguous on this point. Most players interpret it as allowing simultaneous actions."
                    confidence="medium"
                />

                {/* Low Confidence / Unverified */}
                <VerdictCard
                    verdict="This specific scenario is not covered in the rulebook. Consider checking the official FAQ."
                    confidence="low"
                />

                {/* Unverified Quote */}
                <QuoteCard
                    quote="Players may choose to resolve effects in any order they prefer."
                    page={24}
                    verified={false}
                />

                {/* FAQ Citation */}
                <CitationCard
                    sourceType="faq"
                    edition="Official FAQ v2.1 (March 2023)"
                    page={3}
                />

                {/* Errata Citation */}
                <CitationCard
                    sourceType="errata"
                    edition="Errata Document 1.2"
                    sourceUrl="https://example.com/errata.pdf"
                    page={1}
                />
            </div>

            {/* Bottom padding for nav */}
            <div className="h-24" />
        </div>
    );
}
