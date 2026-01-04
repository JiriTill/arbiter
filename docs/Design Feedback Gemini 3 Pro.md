# Design Feedback Gemini 3 Pro 

This is a fantastic start. The implementation of the dark mode, mobile-first layout, and specifically the **"Stacked Card"** architecture on the Verdict page is spot-on. It looks professional, trustworthy, and is easy to parse in seconds, which is exactly what a gamer needs mid-session.

Here is honest, actionable design feedback for your developer to refine the UI/UX before launch.

### **1\. Overall Structure & Theme**

* **✅ The Good:** The dark theme is excellent for game nights. The bottom navigation bar is correctly implemented for mobile. The font choices are clean and readable.  
* **🔧 The Fix:** The bottom navigation bar feels a bit "floating." Add a subtle top border or a very slight background color difference to visually anchor it to the bottom of the screen, separating it from the scrolling content above.

### **2\. The "Ask" Page (Input Flow)**

* **✅ The Good:** The big green submit button is great. The "Trust Signal" banner below it (*"Answers verified against official rulebooks..."*) is a brilliant touch that should definitely stay.  
* **🔧 Critical Fix (Game Selection Hierarchy):** Right now, "Search for a game..." and "Your Question" look like equal, optional fields.  
  * **Problem:** A user might type a question without selecting a game, leading to a bad result.  
  * **Solution:** Visually prioritize the game selection. You could:  
    * Make the Question input **disabled (grayed out)** until a game is selected from the search bar.  
    * Or, number the steps clearly: **"1. Select Game"** and **"2. Ask Question"**.  
* **🔧 Minor Tweaks:**  
  * **Placeholder Text:** Change *"Ask a rules question..."* to something more guiding like, *"e.g., Can I play a Knight before rolling?"*.  
  * **Desktop Tip:** Hide the *"Tip: Press Ctrl+Enter to submit"* text on mobile devices. It's irrelevant clutter on a phone.  
  * **Recent Questions:** The grey "game tag" (e.g., "Catan") inside the recent question card is a bit low-contrast. Make it a distinct badge color (e.g., a muted green or blue) so it pops out as a category label.

### **3\. The "Verdict" Page (The Answer)**

This page is the core of your product, and the stacked design is working perfectly.

* **✅ The Good:** The visual hierarchy is superb.  
  * **The big "YES"** (Instant answer).  
  * **The Quote** (The proof).  
  * **The Source Link** (The deep dive). The "Verified against source" badge with the checkmark is excellent for building trust.  
* **🔧 Critical Fix (Logic & Visual Conflict):**  
  * **Problem:** In your screenshot, you have a big, confident green **"YES"** right next to a red **"Low confidence"** badge. This is confusing and contradictory.  
  * **Solution:** The UI must reflect the logic.  
    * **If Confidence is High:** Show the big Green "YES" / Red "NO" and a Green "High Confidence" badge.  
    * **If Confidence is Low:** Do **not** show a big "YES/NO". Instead, change the header to something like **"Here's what the rules say..."**, provide the quote, and keep the Red "Low confidence" badge. Don't fake certainty.  
* **🔧 UX Refinement (Consolidate Cards):**  
  * **Problem:** The third card ("Rulebook / Standard / Page 11 / View Original") feels repetitive. You already showed the page number in the second card.  
  * **Solution:** Merge Card 2 and Card 3 to save vertical space.  
    * Put the **"View Original"** button with the external link icon directly inside the "From the Rulebook" card, perhaps in the top-right corner next to the "Page 11" badge. This makes the proof and the source link one unified block.

**Summary for Developer:** The foundation is rock solid. Focus on **enforcing the game selection step**, fixing the **conflicting confidence UI** on the verdict page, and **consolidating the source cards** for a tighter mobile layout. Excellent work so far.

