# 🧙 Magic: The Gathering EDH Deck Recommender

## Overview  
This project builds a tool that, given a **Magic: The Gathering EDH decklist**, can **analyze the deck** and **recommend additional cards** to include.  

Magic: The Gathering cards can be complex, and EDH decks consist of 100 unique cards. Currently, there’s no automated tool to assist with the deckbuilding process. This project aims to fill that gap by evaluating decklists and providing intelligent recommendations.

---

## Project Structure

### 1. Card-Tagger  
Available card data is limited to surface-level information and unprocessed string text.  
This component creates a **tagging system** to categorize cards by functionality, enabling meaningful evaluations and algorithmic recommendations.

- Develop a shared **taxonomy and schema** to structure card information  
- Use **LLMs** to tag cards in bulk based on functionality  
- Output a **database of commander-legal cards** with structured tags

---

### 2. Deck-Lists  
This portion focuses on leveraging existing public decklists to power a recommender system.

- Automated **web-scraping** of decklists from community sites  
- Utilize **Archidekt’s public API** to collect deck data  
- Implement scraping pipelines with politeness delays to avoid throttling

---

### 3. Card-Rec (Recommendation Tool)  
The actual user-facing tool, implemented as a **website** with front end, back end, database, and recommendation engine.

- **Front end:** Decklist input, display, and summary UI inspired by existing MTG tools  
- **Back end:** Processes decklists and fetches card data from the **Scryfall API**  
- **Recommendation system:**  
  - Currently: collaborative filtering (recommendations based on community overlap)  
  - Future: tag/synergy-based recommendation algorithm

---

## Key Learnings

### Tagging with LLMs
- Developed a **taxonomy and schema** with 7 categories to structure card functionalities  
- Iterated with an LLM to refine the taxonomy and automate tagging at scale  
- Batched processing to handle 30–40k unique cards efficiently (~$20 in prompt cost)

### Web Scraping
- Learned to scrape and collect **decklist IDs** efficiently  
- Used **Archidekt’s API + scraping** to gather hundreds of decklists  
- Built automated collection with **politeness delays** to avoid getting blocked

### Web Development
- Gained experience setting up a basic **full-stack application**  
- Integrated UI components, database interactions, and recommendation algorithms

---

## Current Setup
- **Taxonomy + schema** provide structured context for LLM extraction  
- Command-line tool supports batch tagging by color identity and batch size  
- Result: Database of every commander-legal card with tags for functional evaluation

---

## Challenges
- **Large dataset:** 30–40k unique cards + card text  
- **Evaluation difficulty:** Some card functions are not easily parsed with regex or simple text extraction and require LLM-based understanding

---

## TODO
- Identify remaining card functions that can be parsed without LLMs  
- Use tagged card data to evaluate decklists in the recommender system  
- Add screenshots, analysis notebooks, and UI examples to the README

---

## Goal  
Tag Magic cards at scale to **evaluate decklists and overall strategies**, enabling more intelligent and automated EDH deck recommendations.

