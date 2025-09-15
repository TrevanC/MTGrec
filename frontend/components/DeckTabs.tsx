'use client';

import { useState } from 'react';
import { DeckState } from '@/lib/types';
import DeckAnalysis from './DeckAnalysis';
import RecommendationsTab from './RecommendationsTab';
import DeckListTab from './DeckListTab';

interface DeckTabsProps {
  deckState: DeckState;
  budgetCents: number;
  onBudgetChange: (budgetCents: number) => void;
  onClearDeck: () => void;
}

export default function DeckTabs({ deckState, budgetCents, onBudgetChange, onClearDeck }: DeckTabsProps) {
  const [activeTab, setActiveTab] = useState<'analysis' | 'recommendations' | 'decklist'>('analysis');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between px-6 py-4">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('analysis')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analysis'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Deck Analysis
            </button>
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'recommendations'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Recommendations
            </button>
            <button
              onClick={() => setActiveTab('decklist')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'decklist'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Deck List
            </button>
          </nav>

          {/* Controls */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label htmlFor="budget" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Budget:
              </label>
              <select
                id="budget"
                value={budgetCents}
                onChange={(e) => onBudgetChange(parseInt(e.target.value))}
                className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value={1000}>$10</option>
                <option value={2500}>$25</option>
                <option value={5000}>$50</option>
                <option value={10000}>$100</option>
                <option value={25000}>$250</option>
                <option value={0}>No limit</option>
              </select>
            </div>

            <button
              onClick={onClearDeck}
              className="text-sm bg-gray-500 text-white px-3 py-1 rounded-md hover:bg-gray-600 transition-colors"
            >
              New Deck
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'analysis' && (
          <DeckAnalysis deckState={deckState} />
        )}
        {activeTab === 'recommendations' && (
          <RecommendationsTab deckState={deckState} />
        )}
        {activeTab === 'decklist' && (
          <DeckListTab deckState={deckState} />
        )}
      </div>
    </div>
  );
}