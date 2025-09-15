# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the MTG EDH/Commander Upgrade Recommender - an application that analyzes Magic: The Gathering EDH/Commander decks and provides upgrade recommendations based on synergy scoring, deck statistics, and community data.

**Architecture:**
- **Frontend:** Next.js (React) - Single page application with session-only deck storage
- **Backend:** FastAPI (Python) - Stateless REST API
- **Database:** PostgreSQL - Stores Scryfall card data and co-occurrence statistics
- **Data Source:** Scryfall bulk data for MTG card information

## Project Structure

This repository is currently in the design phase with comprehensive product specifications in the `docs/` directory:

- `docs/mtg_edh_synergy.md` - Complete product design including user interface wireframes and synergy evaluation methodology
- `docs/mtg_recommender_frontend_backend_design_mvp.md` - Technical MVP specification with API design, database schema, and implementation details

## Key Design Concepts

**Data Model:**
- Cards are stored using the complete Scryfall Card object structure (verbatim)
- Commanders are identified as an attribute of cards (no separate entity)
- Co-occurrence statistics track card relationships for recommendation scoring
- No user deck persistence - decks exist only in browser session storage

**API Design:**
- Stateless endpoints at `/api/v1`
- Key endpoints: `/deck/parse`, `/recommend`, `/cards`
- Uniform error response format with specific error codes
- Scryfall-compatible response structures

**Frontend Flow:**
1. User pastes decklist → parse via API
2. Store parsed deck in session storage
3. Generate recommendations via API
4. Display with configurable explanation levels
5. Optional feedback tracking for analytics

**Synergy Evaluation (Multi-layer):**
- Tag overlap using Scryfall metadata
- Commander-to-card synergy analysis
- Card-to-card resource producer/consumer matching
- Category balance evaluation (enablers vs payoffs)
- Historical co-occurrence from community data

## Development Status

This repository contains design documentation only. Implementation has not yet begun.

When implementation starts, the typical development workflow will be:
- Backend: FastAPI with PostgreSQL, using SQLAlchemy
- Frontend: Next.js with TypeScript, session-based state management
- Testing: Follow standard practices for the chosen frameworks
- Data pipeline: Scryfall bulk data import and processing