Here’s a structured product design draft for the MTG EDH Upgrade Recommender, refined for a **two-tab experience**: one tab for deck analysis and diagnostics, and a second tab for upgrade recommendations — now with full details on how synergy is defined and evaluated.

---

# MTG EDH Upgrade Recommender — Product Design

## Core Concept

An app that analyzes EDH/Commander decks and recommends upgrades by:

1. Diagnosing deck statistics (efficiency, balance, power level).
2. Scoring synergy at multiple levels (commander, card-to-card, archetype).
3. Recommending upgrades or replacements that maximize synergy, efficiency, and budget alignment.

---

## User Input

- **Decklist Import Panel** (appears before analysis)
  - Paste text list.
  - Import from deckbuilding sites (Moxfield, Archidekt, MTGGoldfish).
  - Start with commander + archetype if no list is available.
- **Constraints Sidebar** (persistent across both tabs)
  - Archetype/direction (optional).
  - Power bracket (casual → cEDH).
  - Budget sliders (per card, total deck).
  - Combos allowed toggle.
  - Playgroup meta (optional).

---

## Tab 1: Deck Analysis & Diagnostics

### Section 1: Deck Overview

- Commander portrait + archetype tags at the top.
- Power bracket badge (with tooltip explaining criteria).
- Deck stats preview strip:
  - Mana curve mini-histogram.
  - Color pie mini-chart.
  - Category breakdown bars.

### Section 2: Diagnostics & Red Flags

- Detailed charts:
  - Mana curve histogram (interactive).
  - Full color distribution pie.
  - Category breakdown.
- **Red Flags List**: warnings like “Too few ramp pieces.”

### Section 3: Synergy Insights

- Interactive synergy heatmap.
- Side panel with:
  - **Top Engines Widget** (e.g., Treasure engine).
  - **Weak Links List** (lowest synergy cards).
- Hovering over chart cells shows explanations of synergy strengths and weaknesses.

### Navigation

- Tab switcher at the top: **Deck Analysis | Recommendations**.

---

## Tab 2: Upgrade Recommendations & Tuning

### Section 1: Upgrade Recommendations Table

- Table showing suggested cuts with multiple add options:
  - Columns: [Cut] → [Add Options Dropdown] → [Reason] → [Preview Stats].
  - Each dropdown offers at least three options (premium, mid-range, budget).
- Tabs for filtering inside this tab: [Budget] [Premium] [Theme] [Custom].
- User applies chosen upgrades and sees instant updates to deck metrics.

### Section 2: Updated Deck Stats

- After choices are applied, new charts update:
  - Mana curve.
  - Color balance.
  - Category ratios.
  - Power bracket reevaluation.

### Section 3: Constraints & Fine Tuning

- Inline panel with sliders and toggles:
  - Power level slider.
  - Budget limit.
  - Synergy scoring weight adjustments.
  - Combos allowed toggle.
- Recommendations dynamically update based on new settings.

### Section 4: Export & Sharing

- **Export buttons**: Moxfield, Archidekt.
- **Report Download**: PDF with deck stats, synergy insights, upgrades.
- **Community Sharing**: Option to publish deck report.

### Navigation

- Tab switcher at the top: **Deck Analysis | Recommendations**.

---

## Synergy Evaluation — How It Works

### Layer 1: Tag Overlap (Baseline)

- Uses **Scryfall tags** to align cards with commander and deck theme.
- Cards that share mechanics, tribes, or resources get higher synergy.

### Layer 2: Commander ↔ Card Synergy

- Scores cards that directly enable or benefit from the commander’s ability.
- Example: If commander triggers on lifegain, lifegain enablers get strong synergy boosts.

### Layer 3: Card ↔ Card Synergy

- Matches producers and consumers of the same resource.
  - Token producers ↔ token payoff.
  - Treasure producers ↔ sacrifice/draw payoffs.
- Recognizes tribal overlaps and combo potential (if combos are allowed).

### Layer 4: Category Balance Synergy

- Evaluates ratios of enablers vs. payoffs.
- Penalizes decks with lopsided packages (e.g., many payoffs but no enablers).
- Rewards decks with complete, balanced engines.

### Layer 5: Historical Co-Occurrence

- Draws on EDHREC data to weight card pairs that commonly appear together.
- Can use machine learning clustering to uncover hidden synergies not obvious from tags alone.

### Scoring Formula

**Synergy Score (per card)** =\
`(Commander Alignment × W1) + (Card-Card Overlap × W2) + (Engine Balance × W3) + (Co-Occurrence × W4)`

- **Weights (W1–W4)** are adjustable by the user in the Constraints panel.
- Final deck synergy score is aggregated from individual card scores and package completeness.

---

## Sample User Journey (Two-Tab Flow)

**Step 1: Import Decklist**\
User pastes decklist, sets budget slider, and enables “no combos.”

**Step 2: Deck Analysis Tab**\
They see commander info, stats, red flag warnings, and a synergy heatmap. Weak Links list identifies underperforming cards.

**Step 3: Switch to Recommendations Tab**\
They click the Recommendations tab at the top.

**Step 4: Apply Upgrades**\
The table shows “Cut Hedron Archive → Add Smothering Tithe (premium) / Midnight Clock (mid-range) / Mind Stone (budget).” User selects **Midnight Clock**, and charts update instantly.

**Step 5: Fine-Tune Constraints**\
User adjusts synergy weight sliders, emphasizing card-to-card synergy. Recommendations reshuffle.

**Step 6: Export & Share**\
They export the revised deck to Moxfield and download a PDF upgrade report.

---

## Output

- **Deck Analysis Tab**: Overview, red flags, synergy insights.
- **Recommendations Tab**: Multi-option upgrade list, updated deck metrics, export tools.
- **Synergy Explained**: Transparency on why certain cards are considered synergistic.

---

## Expansion Ideas

- Playgroup-tailored suggestions.
- Guided upgrade path mode.
- AI-driven hidden synergy discovery.
- Social features for comparing decks.

---

## Appendix: Wireframes

### Tab Navigation

```
+-----------------------------------+
| [Deck Analysis] | [Recommendations]|
+-----------------------------------+
```

### Deck Analysis Tab

```
+--------------------------------------------------+
| Commander Image  | Archetype Tags | Power Bracket |
+--------------------------------------------------+
| Mana Curve Histogram | Color Pie | Category Bars |
+--------------------------------------------------+
| Red Flags:                                        |
| - Only 6 ramp pieces (recommend 10–12).           |
| - Mana curve too top-heavy.                       |
+--------------------------------------------------+
| [Synergy Heatmap Visualization]                   |
| Top Engines: Treasure Engine, Token Engine        |
| Weak Links: Hedron Archive, Off-theme Card        |
+--------------------------------------------------+
```

### Recommendations Tab

```
+-------------------------------------------------------------------+
| Cut Card        | Add Options (Dropdown)         | Reason | Stats |
|-------------------------------------------------------------------|
| Hedron Archive  | Smothering Tithe (premium)     | Better | +5%   |
|                 | Midnight Clock (mid-range)     | Curve  | +3%   |
|                 | Mind Stone (budget)            | Ramp   | +2%   |
+-------------------------------------------------------------------+

Updated Deck Stats:
+-----------------------------------------+
| Mana Curve | Color Balance | Categories |
| Power Bracket Reevaluation              |
+-----------------------------------------+
```

### Constraints Panel

```
+-----------------------------------------+
| Power Level Slider [ Casual → cEDH ]    |
| Budget Limit Slider: $___               |
| Combos Allowed: [Yes/No Toggle]         |
| Synergy Weight Adjustments (sliders):   |
| - Commander Alignment                   |
| - Card-to-Card                          |
| - Engine Balance                        |
| - Co-Occurrence                         |
+-----------------------------------------+
```

### Export & Sharing

```
+---------------------------------------------+
| [Export to Moxfield] [Export to Archidekt]  |
| [Download PDF Report] [Share to Community]  |
+---------------------------------------------+
```

---

