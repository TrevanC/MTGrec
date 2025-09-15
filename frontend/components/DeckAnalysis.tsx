'use client';

import { DeckState } from '@/lib/types';
import { getColorIdentitySymbols } from '@/lib/scryfall';

interface DeckAnalysisProps {
  deckState: DeckState;
}

export default function DeckAnalysis({ deckState }: DeckAnalysisProps) {
  if (!deckState.parsed) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400">
        No deck data available
      </div>
    );
  }

  const { parsed } = deckState;

  return (
    <div className="space-y-6">
      {/* Deck Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Commander{parsed.commander_ids.length > 1 ? 's' : ''}
          </h3>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {parsed.commander_ids.length}
          </p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Total Cards
          </h3>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {parsed.commander_ids.length + parsed.card_ids.length}
          </p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Color Identity
          </h3>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">
              {getColorIdentitySymbols(parsed.color_identity)}
            </span>
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {parsed.color_identity.length === 0 ? 'Colorless' :
               parsed.color_identity.length === 1 ? 'Mono-color' :
               parsed.color_identity.length === 2 ? 'Two-color' :
               parsed.color_identity.length === 3 ? 'Three-color' :
               parsed.color_identity.length === 4 ? 'Four-color' :
               'Five-color'}
            </span>
          </div>
        </div>
      </div>

      {/* Issues and Warnings */}
      {parsed.issues.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-3">
            Deck Issues
          </h3>
          <div className="space-y-2">
            {parsed.issues.map((issue, index) => (
              <div key={index} className="flex items-start space-x-2">
                <span className="text-yellow-600 dark:text-yellow-400 mt-0.5">⚠️</span>
                <div>
                  <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                    {issue.text}
                  </p>
                  {issue.suggestions && issue.suggestions.length > 0 && (
                    <div className="mt-1">
                      <p className="text-xs text-yellow-700 dark:text-yellow-300">
                        Suggestions: {issue.suggestions.join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Placeholder for future analysis components */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Detailed Analysis
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900 dark:text-white">Mana Curve</h4>
            <div className="h-32 bg-white dark:bg-gray-800 rounded border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
              <span className="text-gray-500 dark:text-gray-400 text-sm">
                Mana curve visualization (coming soon)
              </span>
            </div>
          </div>
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900 dark:text-white">Category Breakdown</h4>
            <div className="h-32 bg-white dark:bg-gray-800 rounded border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
              <span className="text-gray-500 dark:text-gray-400 text-sm">
                Category breakdown chart (coming soon)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Synergy Analysis Placeholder */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Synergy Insights
        </h3>
        <div className="h-48 bg-white dark:bg-gray-800 rounded border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
          <span className="text-gray-500 dark:text-gray-400 text-sm">
            Synergy heatmap and insights (coming soon)
          </span>
        </div>
      </div>
    </div>
  );
}