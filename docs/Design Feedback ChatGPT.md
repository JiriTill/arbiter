# Design Feedback ChatGPT

I went through the Ask \+ Verdict flow (and your screenshots). **Overall: the UI is already “premium utility” and feels trustworthy.** The structure is right (game → question → big CTA → evidence-first verdict). What’s keeping it from “best-in-class” is mostly **microcopy, confidence signaling, and a couple of clarity/consistency issues**.

Below is **final, developer-ready feedback** (prioritized).

---

## **P0 Must-fix (these directly affect trust/clarity)**

### **1\) “Low confidence” conflicts with “Verified against source”**

On the verdict screen you’re showing:

* **Low confidence** (red badge \+ red-tinted verdict card)

* and **Verified against source** (green signal) with a clean quote \+ page

That combination feels contradictory. Users will ask “If it’s verified, why low confidence?”

**Fix (design-only):**

* Keep **verification** as the primary trust signal.

* Change “Low confidence” to something like:

  * **“Verified quote, but may not cover your exact situation”** or

  * **“Ambiguous / depends on context”**

* Add a tiny “Why?” tooltip/expand line (1 sentence) right under the badge (no long explanations).

**Visual:** make “Low confidence” **amber** instead of red, and remove the aggressive red background glow. Red feels like “wrong”.

---

### **2\) The “Ctrl+Enter” hint is wrong on mobile (and slightly undermines polish)**

On Ask page: “Tip: Press Ctrl+Enter to submit” reads like a desktop-only app.

**Fix:**

* Show that tip **only on desktop**.

* On mobile either remove it or replace with “Tap Ask to submit”.

---

### **3\) Verdict typography / spacing bug: “YES , you can…”**

There’s a visible spacing/punctuation issue (`YES ,`). Small, but it screams “beta”.

**Fix:**

* Render verdicts as “**Yes.** You can…” or “**Yes —** …”

* Avoid ALL CAPS for the whole verdict (caps are louder than needed). Keep one strong keyword.

---

### **4\) The quote card contains odd “Y” characters**

Your quote shows “desert Y… roll a ‘7’ Y… Knight Y…” (looks like highlight markers leaking into text).

**Fix:**

* Don’t inject marker characters into the quote string.

* Use real highlighting:

  * `<mark>` or styled span to highlight the matched phrase (optional)

* Keep the quote readable and copyable.

---

### **5\) The trust strip under the Ask button looks like an input / banner**

The “✓ Answers verified…” bar is good copy, but visually it reads like another UI element you should click.

**Fix:**

* Make it look like **two small badges** (chips) inline:

  * “Verified rulebooks”

  * “Citations”

* Reduce height and border weight so it doesn’t compete with the CTA.

---

## **P1 Strong improvements (high ROI for “A+ feel”)**

### **6\) Ask page needs an explicit “Game” label \+ selected state**

Right now it’s a search bar at top. It’s clean, but it’s easy to miss that selecting the correct game/edition is the most important step for accuracy.

**Fix:**

* Add a small label: **Game**

* After selection, show a compact “selected game chip” like:

  * `Catan (Standard) ✎`  
     This builds confidence before the user even asks.

---

### **7\) Verdict page hierarchy: show “context chips” above the verdict**

You already show `Catan (Standard)` and the question. Consider adding subtle chips under it:

* Source types active (Rulebook / Errata if present)

* Expansions active (later)

Even in beta, it reinforces “I know your context”.

---

### **8\) Quote styling: italic serif looks “fancy” but hurts scanability**

The quote block is aesthetically nice, but italics reduce readability on mobile.

**Fix:**

* Use normal body text \+ blockquote style (left border, slightly lighter text).

* Keep quotes short, but allow “Show more context” expand (design hook).

---

### **9\) Feedback section may be too close to bottom nav**

“Was this helpful?” sits right above the bottom nav and can feel cramped.

**Fix:**

* Add extra bottom padding so it’s never visually “pressed into” the nav.

* Make the thumbs buttons large enough for easy tap.

---

### **10\) Share button placement**

“Share verdict” inside the verdict card is okay, but it competes with the core trust moment.

**Fix:**

* Move share CTA to the **citation/source row** (where it feels “official”), or

* Put it as a secondary action under “View Original”.

---

## **P2 Nice-to-haves (polish, not required)**

### **11\) Recent Questions list is good, but consider a “Show more” fold**

It’s helpful and makes the app feel alive, but it’s also a second goal on the Ask page.

**Fix:**

* Default to 3 items \+ “Show more”.

### **12\) Color system consistency**

Green \= official/verified makes sense.  
 Red should mean “wrong/danger”, not “uncertain”.

**Fix:**

* Green \= verified

* Amber \= uncertain/ambiguous

* Red \= error/unavailable/unsupported

---

## **Summary for the developer (what to change right now)**

If you only do 6 things, do these:

1. Rework “Low confidence” so it **doesn’t fight** the “Verified” signal (amber \+ “why?” line)

2. Remove/replace “Ctrl+Enter” on mobile

3. Fix the “YES ,” rendering and avoid full caps

4. Remove the “Y” artifacts from quotes; use proper highlight styling

5. Turn the trust strip into subtle badges (not a big bar)

6. Add a clear “Game” label \+ selected game chip/edit affordance

