'use client';

import { DeckState } from '@/lib/types';
import RecommendationCard from './RecommendationCard';

interface RecommendationsTabProps {
  deckState: DeckState;
}

export default function RecommendationsTab({ deckState }: RecommendationsTabProps) {
  if (deckState.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Generating recommendations...</p>
        </div>
      </div>
    );
  }

  if (deckState.error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
          Error Loading Recommendations
        </h3>
        <p className="text-red-700 dark:text-red-300">{deckState.error}</p>
      </div>
    );
  }

  if (!deckState.recommendations || deckState.recommendations.recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 dark:text-gray-400 mb-4">
          <svg className="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <p className="text-lg">No recommendations available</p>
        </div>
        <p className="text-gray-400 dark:text-gray-500 text-sm">
          This could be due to limited data or deck composition. Try adjusting your budget or deck list.
        </p>
      </div>
    );
  }

  const { recommendations } = deckState.recommendations;

  return (
    <div className="space-y-6">
      {/* Recommendations Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Upgrade Recommendations
          </h2>
          <p className="text-gray-600 dark:text-gray-300 text-sm mt-1">
            Found {recommendations.length} cards that could improve your deck
          </p>
        </div>

        <div className="text-xs text-gray-500 dark:text-gray-400">
          Algorithm v{deckState.recommendations.algo_version}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          <button className="py-2 px-1 border-b-2 border-blue-500 font-medium text-sm text-blue-600 dark:text-blue-400">
            All Recommendations
          </button>
          <button className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300">
            Budget Friendly
          </button>
          <button className="py-2 px-1 border-b-2 border-transparent font-medium text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300">
            Premium
          </button>
        </nav>
      </div>

      {/* Recommendations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {recommendations.map((recommendation, index) => (
          <RecommendationCard
            key={`${recommendation.card.id}-${index}`}
            recommendation={recommendation}
          />
        ))}
      </div>

      {/* Updated Deck Stats Placeholder */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Deck Improvements Preview
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-24 bg-white dark:bg-gray-800 rounded border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
            <span className="text-gray-500 dark:text-gray-400 text-sm">
              Mana curve improvements
            </span>
          </div>
          <div className="h-24 bg-white dark:bg-gray-800 rounded border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
            <span className="text-gray-500 dark:text-gray-400 text-sm">
              Synergy improvements
            </span>
          </div>
          <div className="h-24 bg-white dark:bg-gray-800 rounded border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
            <span className="text-gray-500 dark:text-gray-400 text-sm">
              Power level estimate
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}