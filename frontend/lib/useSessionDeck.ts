import { useState, useEffect } from 'react';
import { DeckState, ParsedDeck, RecommendationsResponse } from './types';

const STORAGE_KEY = 'mtg-edh-deck-state';

export function useSessionDeck() {
  const [deckState, setDeckState] = useState<DeckState>({
    decklist: '',
    isLoading: false,
  });

  // Load from sessionStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = sessionStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsedState = JSON.parse(stored);
          setDeckState(parsedState);
        }
      } catch (error) {
        console.warn('Failed to load deck state from session storage:', error);
      }
    }
  }, []);

  // Save to sessionStorage when state changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(deckState));
      } catch (error) {
        console.warn('Failed to save deck state to session storage:', error);
      }
    }
  }, [deckState]);

  const updateDeckState = (updates: Partial<DeckState>) => {
    setDeckState(prev => ({ ...prev, ...updates }));
  };

  const setDecklist = (decklist: string) => {
    updateDeckState({
      decklist,
      parsed: undefined,
      recommendations: undefined,
      error: undefined
    });
  };

  const setParsedDeck = (parsed: ParsedDeck) => {
    updateDeckState({
      parsed,
      recommendations: undefined,
      error: undefined
    });
  };

  const setRecommendations = (recommendations: RecommendationsResponse) => {
    updateDeckState({ recommendations, error: undefined });
  };

  const setLoading = (isLoading: boolean) => {
    updateDeckState({ isLoading });
  };

  const setError = (error: string) => {
    updateDeckState({ error, isLoading: false });
  };

  const clearDeck = () => {
    setDeckState({
      decklist: '',
      isLoading: false,
    });
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  };

  return {
    deckState,
    setDecklist,
    setParsedDeck,
    setRecommendations,
    setLoading,
    setError,
    clearDeck,
  };
}