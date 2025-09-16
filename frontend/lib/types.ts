// Scryfall Card object types (based on the API spec)
export interface ScryfallCard {
  id: string;
  oracle_id: string;
  name: string;
  released_at: string;
  set: string;
  set_name: string;
  collector_number: string;
  lang: string;
  cmc: number;
  type_line: string;
  oracle_text?: string;
  colors?: string[];
  color_identity: string[];
  keywords?: string[];
  legalities: Record<string, string>;
  image_uris?: {
    small?: string;
    normal?: string;
    large?: string;
    png?: string;
    art_crop?: string;
    border_crop?: string;
  };
  card_faces?: Array<{
    name: string;
    type_line: string;
    oracle_text?: string;
    colors?: string[];
    image_uris?: {
      small?: string;
      normal?: string;
      large?: string;
      png?: string;
      art_crop?: string;
      border_crop?: string;
    };
  }>;
  prices?: {
    usd?: string;
    usd_foil?: string;
    eur?: string;
    eur_foil?: string;
    tix?: string;
  };
  edhrec_rank?: number;
}

// API Response types
export interface ParsedCard {
  name: string;
  set: string;
  collector_number: string;
  quantity: number;
}

export interface DecklistCard {
  card: ScryfallCard;
  quantity: number;
}

export interface ParsedDeck {
  commander_ids: string[];
  commander_names: string[];
  card_ids: string[];
  color_identity: string[];
  issues: Array<{
    type: string;
    text: string;
    suggestions?: string[];
  }>;
  decklist: DecklistCard[];
}

export interface RecommendationExplanation {
  summary: string;
  reasons: Array<{
    type: string;
    detail: string;
    weight: number;
  }>;
  evidence?: {
    cooc_count: number;
    support_decks: number;
    window_days: number;
  };
  feature_contributions?: Array<{
    feature: string;
    value: number;
    contribution: number;
  }>;
}

export interface Recommendation {
  card: ScryfallCard;
  score: number;
  explanation: RecommendationExplanation;
}

export interface RecommendationsResponse {
  algo_version: string;
  context: {
    commander_ids: string[];
    deck_cards_hash: string;
    color_identity: string[];
    filters: {
      budget_cents: number;
    };
  };
  recommendations: Recommendation[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

// Frontend-specific types
export interface DeckState {
  decklist: string;
  parsed?: ParsedDeck;
  recommendations?: RecommendationsResponse;
  isLoading: boolean;
  error?: string;
}

export interface RecommendationFilters {
  budget_cents: number;
  explain: 'none' | 'preview' | 'full';
  top_k: number;
  explain_top_k: number;
  include_evidence: boolean;
  include_features: boolean;
}