# MTG EDH Recommender — MVP Spec
*Last updated:* September 14, 2025

This document captures the **current design** for the MTG EDH/Commander upgrade recommender MVP using:
- **Frontend:** Next.js (Node.js)
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Data model:** Scryfall **Card** object (verbatim fields)

---

## 1) Product Scope (MVP)
- **Input:** User pastes an existing decklist (no on-site deck construction).
- **State:** Parsed deck **lives only in the browser session** (sessionStorage). No deck persistence on the server.
- **Output:** Ranked upgrade recommendations with built-in explanations.

---

## 2) Backend

### 2.1 Stack & Principles
- FastAPI service at `/api/v1`
- Stateless endpoints: server does **not** store user decks
- Cards are imported from **Scryfall** bulk data and stored in Postgres
- **Commander is an attribute of a Card** (no separate Commander entity)

### 2.2 Data Model (DB)
**Table: `scryfall_cards`** (projected columns for performance + full JSONB)
```sql
CREATE TABLE scryfall_cards (
  id UUID PRIMARY KEY,                -- Scryfall card id
  oracle_id UUID,                     -- stable across printings
  name TEXT NOT NULL,
  released_at DATE,
  set TEXT, set_name TEXT, collector_number TEXT,
  lang TEXT,
  cmc NUMERIC,
  type_line TEXT,
  oracle_text TEXT,
  colors TEXT[],                      -- nullable for multi-face
  color_identity TEXT[] NOT NULL,
  keywords TEXT[],
  legalities JSONB NOT NULL,
  image_uris JSONB,                   -- null when card_faces present
  card_faces JSONB,                   -- for DFC/split/etc
  prices JSONB,
  edhrec_rank INTEGER,
  data JSONB NOT NULL                 -- full Scryfall Card object (verbatim)
);

-- Indexes (illustrative)
CREATE INDEX idx_cards_name_trgm ON scryfall_cards USING gin (name gin_trgm_ops);
CREATE INDEX idx_cards_oracle_text_gin ON scryfall_cards USING gin (to_tsvector('english', coalesce(oracle_text,'')));
CREATE INDEX idx_cards_color_identity ON scryfall_cards USING gin (color_identity);
```

**Commander filter (attribute-based):**
```sql
-- Eligible commanders: Legendary Creature OR cards whose oracle_text includes these phrases.
(lower(type_line) LIKE '%legendary%' AND lower(type_line) LIKE '%creature%')
OR position('can be your commander' IN lower(coalesce(oracle_text,''))) > 0
OR position('as a second commander' IN lower(coalesce(oracle_text,''))) > 0
```

**Co-occurrence stats (for recommendation scoring):**
```sql
CREATE TABLE cooc_stats (
  context_commander_id UUID NOT NULL REFERENCES scryfall_cards(id),
  card_id UUID NOT NULL REFERENCES scryfall_cards(id),
  count BIGINT NOT NULL,
  last_seen DATE NOT NULL,
  PRIMARY KEY (context_commander_id, card_id)
);
CREATE INDEX idx_cooc_commander ON cooc_stats (context_commander_id);
```

**User feedback (optional, anonymous):**
```sql
CREATE TABLE interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id UUID NOT NULL REFERENCES scryfall_cards(id),
  action TEXT CHECK (action IN ('clicked','added','hidden','purchased')),
  ts TIMESTAMP DEFAULT now()
);
```

### 2.3 API Summary
**Base:** `/api/v1` · **Auth:** none (MVP) · **Content-Type:** `application/json`

#### Ops
- `GET /health` → `{ "status": "ok" }`
- `GET /version` → `{ "version": "1.0.0", "git_sha": "...", "build_date": "..." }`

#### Cards (Scryfall-shaped responses)
- `GET /cards` — search & filter (Scryfall field names in items)
  - Query: `q`, `types`, `color_identity`, `only_commanders` (bool), `limit` (<=100), `cursor`
  - Response:
    ```json
    { "items": [ /* list entries using Scryfall Card fields (subset allowed) */ ],
      "next_cursor": null }
    ```
- `GET /cards/{id}` — full **Scryfall Card** object (verbatim fields)

#### Core Flow (stateless)
- `POST /deck/parse` — normalize a pasted decklist
  - **Request**
    ```json
    { "decklist": "Commander Name\nSol Ring\nDockside Extortionist\n..." }
    ```
  - **Response**
    ```json
    {
      "commander_ids": ["<scryfall-uuid>"],
      "card_ids": ["<uuid>", "..."],
      "color_identity": ["R","B"],
      "issues": [{ "type":"unknown_card", "text":"...", "suggestions":["..."] }]
    }
    ```

- `POST /recommend` — **ranked adds + explanations (combined)**
  - **Request**
    ```json
    {
      "commander_ids": ["<uuid>"],
      "deck_card_ids": ["<uuid>", "..."],
      "budget_cents": 2000,
      "top_k": 20,
      "explain": "full",            // "none" | "preview" | "full" (default: "full")
      "explain_top_k": 10,          // full explanations for top N
      "include_evidence": false,    // heavy stats like counts/windows
      "include_features": false     // per-feature contributions (debug)
    }
    ```
  - **Response (shape)**
    ```json
    {
      "algo_version": "2025-09-14a",
      "context": {
        "commander_ids": ["<uuid>"],
        "deck_cards_hash": "sha256:...",
        "color_identity": ["R","B"],
        "filters": { "budget_cents": 2000 }
      },
      "recommendations": [
        {
          "card": {
            "id": "<uuid>",
            "name": "Smothering Tithe",
            "prices": { "usd": "12.00" },
            "image_uris": { "normal": "..." }
          },
          "score": 8421,
          "explanation": {
            "summary": "Pairs with Dockside; fills ramp gap",
            "reasons": [
              { "type":"co_occurrence", "detail":"Seen with Prosper in 68% of lists (90d)", "weight":0.62 },
              { "type":"curve_fit", "detail":"Improves CMC 2–3 ramp gap", "weight":0.18 }
            ],
            "evidence": { "cooc_count": 532, "support_decks": 4210, "window_days": 90 },
            "feature_contributions": [
              { "feature":"pmi(commander,card)", "value":2.13, "contribution":0.41 }
            ]
          }
        }
      ]
    }
    ```

- `POST /feedback` — non-blocking UX signals
  - **Request**: `{ "card_id":"<uuid>", "action":"clicked" | "added" | "hidden" | "purchased" }`
  - **Response**: `{ "ok": true }`

### 2.4 Rec Algorithm (MVP)
- Candidates by **co-occurrence** with commander and deck core (`cooc_stats`), filtered by color identity and optional budget
- Score: `count` (MVP) → (later) blend with curve/category gaps, penalties, recency
- Explanations are derived from the same features (preview vs full controlled by params)

---

## 3) Frontend

### 3.1 Stack & Principles
- **Next.js (React)** single page flow
- **Session-only**: parsed deck kept in `sessionStorage`
- Talks to backend using `/deck/parse` → `/recommend`

### 3.2 Key Files (suggested)
```
app/page.tsx                    # Main flow: paste → parse → recommend
components/DeckInput.tsx        # Textarea + submit
components/RecommendationCard.tsx
lib/api.ts                      # API client (fetch)
lib/types.ts                    # Scryfall + API types
lib/scryfall.ts                 # image/price helpers
lib/useSessionDeck.ts           # session storage hook
```

### 3.3 Client Flow
1) User pastes decklist → **POST `/deck/parse`**
2) Store response in session; show issues/color identity
3) Build payload and call **POST `/recommend`** (choose `explain` level)
4) Render recommendation cards using `card.image_uris` or `card.card_faces[].image_uris`
5) Fire **`POST /feedback`** on interactions (optional; non-blocking)

### 3.4 Controls (UI)
- **Budget (USD)** → maps to `budget_cents`
- **Explanation level** → `"full" | "preview" | "none"`
- **Re-run recommendations** button

### 3.5 ENV
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 4) Non-Functional
- **CORS**: allow frontend origin
- **Performance**: keep `/recommend` under ~400ms P95 for top_k=20 with `preview`; use `explain_top_k` to bound cost
- **Error shape** (uniform):
```json
{ "error": { "code": "NOT_FOUND|VALIDATION_ERROR|UNPROCESSABLE_ENTITY|INTERNAL_ERROR", "message": "..." } }
```

---

## 5) Future Enhancements (optional)
- Add curve/category balancing features
- Personalization via feedback signals
- Cached `rec_session_id` to speed up explanations
- Cursor pagination on `/cards` using Scryfall-style list wrappers

