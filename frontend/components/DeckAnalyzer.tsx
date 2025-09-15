'use client';

import { useState } from 'react';
import { useSessionDeck } from '@/lib/useSessionDeck';
import { api } from '@/lib/api';
import DeckInput from './DeckInput';
import DeckTabs from './DeckTabs';

export default function DeckAnalyzer() {
  const {
    deckState,
    setDecklist,
    setParsedDeck,
    setRecommendations,
    setLoading,
    setError,
    clearDeck,
  } = useSessionDeck();

  const [budgetCents, setBudgetCents] = useState(5000); // $50 default

  const handleDecklistSubmit = async (decklist: string) => {
    setDecklist(decklist);
    setLoading(true);

    try {
      // Parse the decklist
      const parsed = await api.parseDeck(decklist);
      setParsedDeck(parsed);

      // If parsing was successful and we have cards, get recommendations
      if (parsed.card_ids.length > 0 && parsed.commander_ids.length > 0) {
        const recommendations = await api.getRecommendations(
          parsed.commander_ids,
          parsed.card_ids,
          { budget_cents: budgetCents }
        );
        setRecommendations(recommendations);
      }
    } catch (error) {
      console.error('Error processing deck:', error);
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBudgetChange = async (newBudgetCents: number) => {
    setBudgetCents(newBudgetCents);

    // Re-run recommendations if we have a parsed deck
    if (deckState.parsed && deckState.parsed.card_ids.length > 0) {
      setLoading(true);
      try {
        const recommendations = await api.getRecommendations(
          deckState.parsed.commander_ids,
          deckState.parsed.card_ids,
          { budget_cents: newBudgetCents }
        );
        setRecommendations(recommendations);
      } catch (error) {
        console.error('Error updating recommendations:', error);
        if (error instanceof Error) {
          setError(error.message);
        }
      } finally {
        setLoading(false);
      }
    }
  };

  const handleClearDeck = () => {
    clearDeck();
  };

  return (
    <div className="max-w-7xl mx-auto">
      {!deckState.parsed ? (
        <DeckInput
          onSubmit={handleDecklistSubmit}
          isLoading={deckState.isLoading}
          error={deckState.error}
          initialDecklist={deckState.decklist}
        />
      ) : (
        <DeckTabs
          deckState={deckState}
          budgetCents={budgetCents}
          onBudgetChange={handleBudgetChange}
          onClearDeck={handleClearDeck}
        />
      )}
    </div>
  );
}