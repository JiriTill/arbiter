# Design Feedback Claude Sonnet 4.5

# **Comprehensive Design & UI Feedback for The Arbiter**

I tested the live app at [https://arbiter-sage.vercel.app/ask](https://arbiter-sage.vercel.app/ask) and reviewed your screenshots. Here's my honest, final feedback organized by priority.

---

## **🔴 CRITICAL ISSUES (Must Fix Before Launch)**

### **1\. Ask Page: Game Selection UX is Confusing**

**Problem:** The search bar says "Search for a game..." but there's no visual indication of:

* Whether a game is currently selected  
* How to see the selected game  
* How to change games after selection

**Fix:**

Replace the search input with a proper game selector button:

Before typing:  
┌─────────────────────────────────────┐  
│ 🎲 Select a game...            ▼   │  
└─────────────────────────────────────┘

After selection:  
┌─────────────────────────────────────┐  
│ 🎲 Catan (Standard)            ▼   │  
│    2 sources verified          ✓   │

└─────────────────────────────────────┘

**Rationale:** Users need to know what game context they're asking about at all times.

---

### **2\. Verdict Page: Confidence Badge is Too Subtle**

**Problem:** The "Low confidence" badge (red pill) is small and tucked in the corner. This is THE most important trust signal and it's barely noticeable.

**Fix:**

Make confidence a primary visual element:

LOW CONFIDENCE ANSWER  
┌─────────────────────────────────────────────────┐  
│  ⚠️  THE VERDICT                                 │  
│                                                  │  
│  YES, you can move the robber by rolling a '7'  │  
│  or playing a Knight card.                      │  
│                                                  │  
│  ⚠️  This answer has low confidence. Multiple   │  
│     interpretations possible. Verify rulebook.  │

└─────────────────────────────────────────────────┘

**Rationale:** Low confidence \= user should double-check. Don't hide this information.

---

### **3\. Verdict Page: Visual Hierarchy is Inverted**

**Problem:** The quote card is MORE prominent (larger, darker background) than the verdict itself. Users scan the quote first, then read the verdict.

**Fix:**

* Verdict card: Larger text (text-xl or text-2xl), brighter background (`#1a1a1a` → `#252525`)  
* Quote card: Smaller text (text-base), less contrast (`#0f2315` → `#1a1a1a`)  
* Make the verdict visually "heavier" than supporting evidence

**Rationale:** Answer \> Evidence in visual weight.

---

## **🟡 HIGH PRIORITY (Strongly Recommended)**

### **4\. Ask Page: "Ask The Arbiter" Button Text is Redundant**

**Problem:** The button says "Ask The Arbiter" but you're already in "Ask The Arbiter" app. It's like a "Gmail" button inside Gmail.

**Fix:**

Change button text to action-oriented:

┌─────────────────────────────┐  
│  → Get Answer               │  
└─────────────────────────────┘

Or simpler:  
┌─────────────────────────────┐  
│  Ask                        │

└─────────────────────────────┘

---

### **5\. Verdict Page: Missing Expansion Context**

**Problem:** The header shows "Catan (Standard)" but if the user had selected expansions, there's no indication which rules are active.

**Fix:**

Add expansion badges when relevant:

Catan (Standard)  
🔹 Cities & Knights  🔹 Seafarers

How do you move the robber?

---

### **6\. Recent Questions: Timestamp is Too Precise**

**Problem:** "2 min ago" is fine, but board game sessions last hours. After 30 minutes, "30 min ago" feels oddly specific.

**Fix:**

Use casual time buckets:  
\- Just now (\< 1 min)  
\- A few minutes ago (1-5 min)  
\- Recently (5-30 min)  
\- Earlier today (30 min \- 6 hours)  
\- Today (6-24 hours)  
\- Yesterday  
\- This week

\- \[Date\] (older)

---

### **7\. Verdict Card: "YES" Color Coding is Misleading**

**Problem:** The verdict says "YES" in bright green, which screams "HIGH CONFIDENCE" even though the badge says "Low confidence". Color signals contradict each other.

**Fix:**

For low confidence answers:  
\- Don't color-code the YES/NO/DEPENDS text  
\- Keep it white/neutral  
\- Let the confidence badge be the ONLY trust signal

Or use muted colors:  
\- High confidence: bright green YES  
\- Medium confidence: white YES

\- Low confidence: gray/muted YES

---

## **🟢 MEDIUM PRIORITY (Polish)**

### **8\. Quote Card: "FROM THE RULEBOOK" is Too Loud**

**Problem:** All caps \+ icon \+ "Verified against source" is three layers of the same information.

**Fix:**

Simplify to:

┌─────────────────────────────────────┐  
│  📖 Rulebook, Page 11               │  
│                                      │  
│  "The robber begins the game in..." │  
│                                      │  
│  ✓ Verified                         │

└─────────────────────────────────────┘

---

### **9\. Verdict Page: "Ask another question" is Ambiguous**

**Problem:** Does this go back to ask the same game? Or start over completely?

**Fix:**

Be explicit:

← Ask about Catan

Or with icon context:

← Ask another Catan question

---

### **10\. Ask Page: Info Text is Low Contrast**

**Problem:** "✓ Answers verified against official rulebooks • Citations included" is hard to read (gray on dark).

**Fix:**

* Increase contrast slightly (current looks like `#6b7280`, try `#9ca3af`)  
* Or add subtle border/background to make it a proper badge  
* Or move it closer to the button as a trust signal

---

### **11\. Recent Questions: No Visual Feedback on Tap**

**Problem:** The question cards look tappable but don't show hover/active states clearly.

**Fix:**

css  
.recent-question {  
  transition: background 150ms;  
}  
.recent-question:hover {  
  background: \#1f1f1f; */\* slightly lighter \*/*  
}  
.recent-question:active {  
  background: \#2a2a2a;  
  transform: scale(0.99);  
}  
\`\`\`

\---

\#\#\# 12. \*\*Verdict Page: "Share verdict" Button is Hidden\*\*  
\*\*Problem:\*\* The share button is tucked at the bottom of the verdict card in small text. Sharing \= growth \= important.

\*\*Fix:\*\*  
\`\`\`  
Make it a prominent secondary action:

Top right of verdict card:  
\[Share verdict 🔗\]  (ghost button style)

Or after the citation:  
┌──────────────────────────────────┐  
│  🔗 Share this ruling            │  
└──────────────────────────────────┘  
\`\`\`

\---

\#\# 🔵 LOW PRIORITY (Nice to Have)

\#\#\# 13. \*\*Ask Page: Empty State Could Be More Engaging\*\*  
\*\*Current:\*\* Blank textarea with placeholder  
\*\*Better:\*\* Show example questions or quick-start tips  
\`\`\`  
Your Question  
┌─────────────────────────────────────────────┐  
│ Ask a rules question...                     │  
│                                              │  
│ 💡 Try: "Can I trade with the bank?"        │  
│        "How does the robber work?"          │  
│        "When do I draw development cards?"  │  
└─────────────────────────────────────────────┘  
\`\`\`

\---

\#\#\# 14. \*\*Verdict Page: Page Number Could Be More Actionable\*\*  
\*\*Current:\*\* "Page 11" is just text  
\*\*Better:\*\* Make it feel interactive  
\`\`\`  
📄 Page 11  →  \[View in PDF\]  
\`\`\`

\---

\#\#\# 15. \*\*Bottom Nav: "Ask" Icon is a Question Mark\*\*  
\*\*Problem:\*\* Question mark typically means "help" not "ask a question"  
\*\*Better:\*\* Use a chat bubble, microphone, or search icon  
\`\`\`  
Current: ?  →  Better: 💬 or 🔍  
\`\`\`

\---

\#\#\# 16. \*\*Typography: Serif for Quotes Feels Old-School\*\*  
\*\*Current:\*\* Quotes use Georgia (serif italic)  
\*\*Suggestion:\*\* Consider a modern serif like Newsreader or Lora, or even keep sans-serif for consistency

This is subjective, but board gamers skew younger and expect modern interfaces.

\---

\#\# 🎨 COLOR SYSTEM FEEDBACK

Your color usage is mostly good, but needs refinement:

\#\#\# Current Colors:  
\- Background: \#0a0a0a ✓ Good  
\- Cards: \#1a1a1a ✓ Good    
\- Text: White/off-white ✓ Good  
\- Green (button): \#4ade80 ✓ Good  
\- Red (low confidence): Unclear (looks orange-ish in screenshot)

\#\#\# Recommendations:  
\`\`\`  
Confidence Colors:  
\- High: \#22c55e (green-500) \- current is good  
\- Medium: \#f59e0b (amber-500) \- distinct from both  
\- Low: \#ef4444 (red-500) \- actual red, not orange

Interactive States:  
\- Default button: \#4ade80 ✓  
\- Hover: \#22c55e (darker green)  
\- Pressed: \#16a34a (even darker)  
\- Disabled: \#374151 (gray)

Make sure all text meets WCAG AA contrast (4.5:1).  
\`\`\`

\---

\#\# 📱 MOBILE-SPECIFIC ISSUES

\#\#\# 17. \*\*Verdict Cards: Too Much Scrolling\*\*  
\*\*Problem:\*\* On iPhone SE (375px width), you have to scroll past the verdict to see the quote, then scroll again for citation.

\*\*Fix:\*\*  
\- Reduce padding in cards (p-6 → p-4)  
\- Smaller font sizes on mobile (text-base → text-sm for body)  
\- Consider collapsible sections for less critical info

\---

\#\#\# 18. \*\*Ask Page: Keyboard Covers Button\*\*  
\*\*Problem:\*\* On iOS, when keyboard opens, the "Ask" button might be hidden.

\*\*Fix:\*\*  
\- Use \`viewport-fit=cover\` meta tag  
\- Add extra bottom padding (safe-area-inset-bottom)  
\- Or make button sticky when keyboard is open

\---

\#\# 🎯 INFORMATION ARCHITECTURE

\#\#\# 19. \*\*Missing: Game/Edition Visibility in Verdict\*\*  
\*\*Current:\*\* "Catan (Standard)" is shown but edition isn't clear  
\*\*Better:\*\* Be explicit about which version  
\`\`\`  
🎲 Catan (5th Edition, 2015)  
📦 Base game only  
\`\`\`

This prevents confusion when rules differ between editions.

\---

\#\#\# 20. \*\*Missing: Source Version/Date\*\*  
\*\*Current:\*\* "Rulebook, Page 11"  
\*\*Better:\*\* "Rulebook (2020 revision), Page 11"

Rules get updated. Show which version was used.

\---

\#\# 🏆 WHAT'S ALREADY GREAT

Don't change these:

✅ \*\*Dark theme\*\* \- Perfect for gaming sessions    
✅ \*\*Clean, uncluttered layout\*\* \- No visual noise    
✅ \*\*Stacked card design\*\* \- Easy to scan    
✅ \*\*Bottom navigation\*\* \- Thumb-friendly    
✅ \*\*Green CTA button\*\* \- High contrast, action-oriented    
✅ \*\*Recent questions\*\* \- Good discovery feature    
✅ \*\*Verified badge\*\* \- Builds trust  

\---

\#\# 📋 FINAL PRIORITY CHECKLIST FOR DEVELOPER

Tell Antigravity to implement in this order:

\#\#\# Must Do (Before Launch):  
\- \[ \] Fix game selector to show current selection clearly  
\- \[ \] Make confidence badge more prominent (especially for LOW)  
\- \[ \] Adjust visual hierarchy (verdict \> quote in prominence)  
\- \[ \] Fix YES/NO color coding for low confidence answers  
\- \[ \] Add expansion context when relevant

\#\#\# Should Do (Week 1 After Launch):  
\- \[ \] Change button text to "Get Answer" or "Ask"  
\- \[ \] Improve recent questions hover states  
\- \[ \] Simplify quote card header  
\- \[ \] Make "Share verdict" more prominent  
\- \[ \] Fix timestamp buckets

\#\#\# Nice to Have (Future):  
\- \[ \] Add example questions to empty state  
\- \[ \] Make page numbers more interactive  
\- \[ \] Consider typography updates  
\- \[ \] Mobile keyboard handling improvements

\---

\#\# 🎨 MOCKUP SUGGESTIONS

For critical issues, here's what to tell Antigravity:  
\`\`\`  
PRIORITY 1: Update game selector on Ask page

Change from:  
\[Search input that hides selection\]

To:  
\[Button showing: "🎲 Catan (5th Edition) ▼" with green checkmark\]  
Click opens modal with:  
\- Game list  
\- Edition selector  
\- Expansion checkboxes  
\- "Preload sources" button

\---

PRIORITY 2: Redesign verdict card for low confidence

Current layout keeps the verdict text the same size, but add a warning banner:

┌─────────────────────────────────────────────┐  
│ ⚠️ LOW CONFIDENCE ANSWER                    │  
├─────────────────────────────────────────────┤  
│                                              │  
│ YES, you can move the robber by rolling     │  
│ a '7' or playing a Knight card.             │  
│                                              │  
│ This answer may have multiple valid         │  
│ interpretations. Double-check the           │  
│ rulebook if the stakes are high.            │  
│                                              │  
└─────────────────────────────────────────────┘

\---

PRIORITY 3: Adjust card backgrounds for hierarchy

\- Verdict card: \#252525 (lighter)  
\- Quote card: \#1a1a1a (darker)  
\- Citation card: \#1a1a1a (same as quote)

Make the most important card (verdict) visually "lift" above others.

---

## **🎬 FINAL THOUGHTS**

**The app looks clean and professional.** The dark theme, card layout, and overall structure are solid. The issues are mostly about **information hierarchy** and **trust signals**.

**The biggest risk:** Users might not notice confidence levels and trust low-confidence answers too much. Make confidence LOUD and CLEAR.

**The biggest opportunity:** The design is 80% there. These refinements will take it to 95%+.

**Ship timeline:** With these changes, you're production-ready in 2-3 days of focused UI work.

Good luck with launch\! 🚀🎲

