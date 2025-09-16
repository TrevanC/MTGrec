import { ParsedDeck, RecommendationsResponse, RecommendationFilters, ApiError, ScryfallCard } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

class ApiError extends Error {
  constructor(public code: string, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData: ApiError = await response.json();
      throw new ApiError(errorData.error.code, errorData.error.message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('NETWORK_ERROR', 'Failed to communicate with the API');
  }
}

export const api = {
  // Health check
  async getHealth(): Promise<{ status: string }> {
    return apiRequest('/health');
  },

  // Parse decklist
  async parseDeck(decklist: string, commander1?: string, commander2?: string): Promise<ParsedDeck> {
    return apiRequest('/deck/parse', {
      method: 'POST',
      body: JSON.stringify({ 
        decklist, 
        commander1: commander1 || null, 
        commander2: commander2 || null 
      }),
    });
  },

  // Get recommendations
  async getRecommendations(
    commander_ids: string[],
    deck_card_ids: string[],
    filters: Partial<RecommendationFilters> = {}
  ): Promise<RecommendationsResponse> {
    const payload = {
      commander_ids,
      deck_card_ids,
      budget_cents: filters.budget_cents || 5000,
      top_k: filters.top_k || 20,
      explain: filters.explain || 'full',
      explain_top_k: filters.explain_top_k || 10,
      include_evidence: filters.include_evidence || false,
      include_features: filters.include_features || false,
    };

    return apiRequest('/deck/recommend', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Search cards
  async searchCards(params: {
    q?: string;
    types?: string;
    color_identity?: string;
    only_commanders?: boolean;
    limit?: number;
    cursor?: string;
  } = {}): Promise<{ items: ScryfallCard[]; next_cursor?: string }> {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value));
      }
    });

    const query = searchParams.toString();
    return apiRequest(`/cards${query ? '?' + query : ''}`);
  },

  // Get card by ID
  async getCard(id: string): Promise<ScryfallCard> {
    return apiRequest(`/cards/${id}`);
  },

  // Submit feedback
  async submitFeedback(card_id: string, action: 'clicked' | 'added' | 'hidden' | 'purchased'): Promise<{ ok: boolean }> {
    return apiRequest('/feedback', {
      method: 'POST',
      body: JSON.stringify({ card_id, action }),
    });
  },
};