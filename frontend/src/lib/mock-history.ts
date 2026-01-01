// Mock history data for testing the History page
// This will be replaced with real data from the API/context later

export type Confidence = "high" | "medium" | "low";
export type SourceType = "rulebook" | "faq" | "errata";

export interface HistoryEntry {
    id: string;
    // Question info
    question: string;
    gameId: string;
    gameName: string;
    gameEdition: string;
    timestamp: Date;

    // Answer info
    verdict: string;
    confidence: Confidence;

    // Citation info
    quote: string;
    quotePage: number;
    quoteVerified: boolean;
    sourceType: SourceType;
    sourceEdition: string;
    sourceUrl?: string;

    // Optional superseded rule
    superseded?: {
        oldQuote: string;
        oldPage: number;
        reason: string;
    };
}

// Helper to create timestamps relative to "now"
const hoursAgo = (hours: number) => new Date(Date.now() - hours * 60 * 60 * 1000);
const daysAgo = (days: number) => new Date(Date.now() - days * 24 * 60 * 60 * 1000);

export const MOCK_HISTORY: HistoryEntry[] = [
    {
        id: "1",
        question: "Can I trade with the bank at 2:1 if I have a harbor?",
        gameId: "catan",
        gameName: "Catan",
        gameEdition: "5th Edition",
        timestamp: hoursAgo(0.03), // ~2 minutes ago
        verdict: "Yes, you can trade with the bank at a 2:1 ratio if you have the matching port.",
        confidence: "high",
        quote: "A player who has built a settlement at a harbor can trade with the bank at a more favorable rate. A 2:1 harbor allows the player to trade 2 resource cards of the type shown for any 1 other resource card.",
        quotePage: 12,
        quoteVerified: true,
        sourceType: "rulebook",
        sourceEdition: "Catan 5th Edition (2015)",
        sourceUrl: "https://example.com/catan-rules.pdf",
        superseded: {
            oldQuote: "Trading with the bank always requires 4 identical resource cards for 1 resource card of your choice.",
            oldPage: 8,
            reason: "The base trading rule on page 8 is modified by the harbor rules on page 12.",
        },
    },
    {
        id: "2",
        question: "Does the robber block resource production for all players or just the one who placed it?",
        gameId: "catan",
        gameName: "Catan",
        gameEdition: "5th Edition",
        timestamp: hoursAgo(1.5),
        verdict: "The robber blocks production for ALL players with settlements on that hex, including the player who placed it.",
        confidence: "high",
        quote: "If a player has built a settlement or city on a hex with the robber, that player does not receive any resources from that hex.",
        quotePage: 9,
        quoteVerified: true,
        sourceType: "rulebook",
        sourceEdition: "Catan 5th Edition (2015)",
    },
    {
        id: "3",
        question: "Can I claim multiple routes between the same two cities?",
        gameId: "ticket-to-ride",
        gameName: "Ticket to Ride",
        gameEdition: "Europe",
        timestamp: hoursAgo(5),
        verdict: "In games with 2-3 players, only one route between cities can be claimed. With 4+ players, all routes are available.",
        confidence: "high",
        quote: "Double routes: In 2 or 3 player games, only one of the two routes can be used. The other route is closed. In 4-5 player games, both routes can be claimed, but not by the same player.",
        quotePage: 4,
        quoteVerified: true,
        sourceType: "rulebook",
        sourceEdition: "Ticket to Ride: Europe (2005)",
    },
    {
        id: "4",
        question: "When exactly do I score bonus points for eggs in Wingspan?",
        gameId: "wingspan",
        gameName: "Wingspan",
        gameEdition: "2nd Printing",
        timestamp: daysAgo(1),
        verdict: "Eggs are scored at the end of the game. Each egg on a bird card is worth 1 victory point.",
        confidence: "medium",
        quote: "At end of game, score 1 point per egg on your birds.",
        quotePage: 10,
        quoteVerified: true,
        sourceType: "rulebook",
        sourceEdition: "Wingspan Rulebook (2019)",
    },
    {
        id: "5",
        question: "Can I use a rest action if I have no cards to recover in Gloomhaven?",
        gameId: "gloomhaven",
        gameName: "Gloomhaven",
        gameEdition: "2nd Edition",
        timestamp: daysAgo(2),
        verdict: "Yes, you can rest even with no discarded cards. A short rest recovers one random card from your discard, while a long rest heals you and lets you choose which card to lose.",
        confidence: "low",
        quote: "A character can perform a rest at any time, even if there are no cards in their discard pile.",
        quotePage: 24,
        quoteVerified: false,
        sourceType: "faq",
        sourceEdition: "Official FAQ v1.8",
    },
    {
        id: "6",
        question: "What happens if I draw an epidemic card as my last card in Pandemic?",
        gameId: "pandemic",
        gameName: "Pandemic",
        gameEdition: "Base Game",
        timestamp: daysAgo(5),
        verdict: "Resolve the epidemic normally. The infection phase still happens after your turn ends.",
        confidence: "high",
        quote: "When you draw an Epidemic card, immediately resolve its effects. Then draw any remaining cards to fill your hand.",
        quotePage: 7,
        quoteVerified: true,
        sourceType: "rulebook",
        sourceEdition: "Pandemic Rules (2013)",
    },
];

// Helper to format relative timestamps
export function formatRelativeTime(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
