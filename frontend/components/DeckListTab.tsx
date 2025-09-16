'use client';

import React, { useState } from 'react';
import { DeckState, DecklistCard } from '@/lib/types';

interface DeckListTabProps {
  deckState: DeckState;
}

export default function DeckListTab({ deckState }: DeckListTabProps) {
  const [hoveredCard, setHoveredCard] = useState<DecklistCard | null>(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });

  if (!deckState.parsed || !deckState.parsed.decklist) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400">
        No deck data available
      </div>
    );
  }

  const { decklist } = deckState.parsed;

  // Function to categorize cards by type_line
  const categorizeCard = (decklistCard: DecklistCard): string => {
    const typeLine = decklistCard.card.type_line?.toLowerCase() || '';
    
    // Check if this card is a commander (only cards entered in commander input fields)
    const isCommander = deckState.parsed?.commander_names?.includes(decklistCard.card.name) || false;
    
    if (isCommander) {
      return 'Commander';
    }
    
    // Creature overrides all other types
    if (typeLine.includes('creature')) {
      return 'Creature';
    }
    
    // Land overrides other types (but not creature)
    if (typeLine.includes('land')) {
      return 'Land';
    }
    
    // Other major types
    if (typeLine.includes('instant')) {
      return 'Instant';
    }
    if (typeLine.includes('sorcery')) {
      return 'Sorcery';
    }
    if (typeLine.includes('artifact')) {
      return 'Artifact';
    }
    if (typeLine.includes('enchantment')) {
      return 'Enchantment';
    }
    if (typeLine.includes('battle')) {
      return 'Battle';
    }
    if (typeLine.includes('planeswalker')) {
      return 'Planeswalker';
    }
    
    return 'Other';
  };

  // Group cards by type
  const groupedByType = decklist.reduce((acc, decklistCard) => {
    const type = categorizeCard(decklistCard);
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(decklistCard);
    return acc;
  }, {} as Record<string, DecklistCard[]>);

  // Define the order for displaying types
  const typeOrder = ['Commander', 'Creature', 'Land', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Battle', 'Planeswalker', 'Other'];
  
  // Sort types according to the defined order
  const sortedTypes = typeOrder.filter(type => groupedByType[type] && groupedByType[type].length > 0);

  const totalCards = decklist.reduce((sum, card) => sum + card.quantity, 0);
  const uniqueCards = decklist.length;

  const handleMouseEnter = (decklistCard: DecklistCard, event: React.MouseEvent) => {
    setHoveredCard(decklistCard);
    setHoverPosition({ x: event.clientX, y: event.clientY });
  };

  const handleMouseLeave = () => {
    setHoveredCard(null);
  };

  const getCardImageUrl = (card: DecklistCard['card']) => {
    // Try different image URI sizes in order of preference
    if (card.image_uris?.normal) return card.image_uris.normal;
    if (card.image_uris?.large) return card.image_uris.large;
    if (card.image_uris?.small) return card.image_uris.small;
    if (card.image_uris?.png) return card.image_uris.png;
    
    // For double-faced cards, try the first face
    if (card.card_faces && card.card_faces.length > 0) {
      const firstFace = card.card_faces[0];
      if (firstFace.image_uris?.normal) return firstFace.image_uris.normal;
      if (firstFace.image_uris?.large) return firstFace.image_uris.large;
      if (firstFace.image_uris?.small) return firstFace.image_uris.small;
      if (firstFace.image_uris?.png) return firstFace.image_uris.png;
    }
    
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Summary
        </h4>
        
        {/* Overall Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
          <div>
            <span className="text-gray-600 dark:text-gray-400">Unique Cards:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-white">
              {uniqueCards}
            </span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Total Cards:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-white">
              {totalCards}
            </span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Most Copies:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-white">
              {Math.max(...decklist.map(decklistCard => decklistCard.quantity))}x
            </span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Singletons:</span>
            <span className="ml-2 font-medium text-gray-900 dark:text-white">
              {decklist.filter(decklistCard => decklistCard.quantity === 1).length}
            </span>
          </div>
        </div>

        {/* Type Breakdown */}
        <div>
          <h5 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
            By Type
          </h5>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 text-xs">
            {sortedTypes.map(type => {
              const cards = groupedByType[type];
              const totalCards = cards.reduce((sum, decklistCard) => sum + decklistCard.quantity, 0);
              return (
                <div key={type} className="bg-gray-100 dark:bg-gray-600 rounded px-2 py-1">
                  <div className="font-medium text-gray-800 dark:text-gray-200">{type}</div>
                  <div className="text-gray-600 dark:text-gray-400">
                    {cards.length} unique, {totalCards} total
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Deck List ({totalCards} cards)
        </h3>
      </div>

      {/* Deck List */}
      <div className="space-y-6">
        {sortedTypes.map(type => {
          const cards = groupedByType[type];
          const totalCards = cards.reduce((sum, decklistCard) => sum + decklistCard.quantity, 0);
          
          return (
            <div key={type} className="space-y-3">
              <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-300 dark:border-gray-600 pb-2">
                {type} ({cards.length} unique, {totalCards} total)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {cards
                  .sort((a, b) => {
                    // Sort by quantity first (descending), then by name
                    if (a.quantity !== b.quantity) {
                      return b.quantity - a.quantity;
                    }
                    return a.card.name.localeCompare(b.card.name);
                  })
                  .map((decklistCard, index) => (
                    <div
                      key={`${decklistCard.card.name}-${index}`}
                      className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded-lg px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors cursor-pointer"
                      onMouseEnter={(e) => handleMouseEnter(decklistCard, e)}
                      onMouseLeave={handleMouseLeave}
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {decklistCard.card.name}
                        </span>
                        <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {decklistCard.card.set && decklistCard.card.collector_number 
                            ? `${decklistCard.card.set} ${decklistCard.card.collector_number}`
                            : decklistCard.card.set || decklistCard.card.collector_number || 'No set info'
                          }
                        </div>
                        {decklistCard.card.type_line && (
                          <div className="text-xs text-gray-400 dark:text-gray-500 truncate italic">
                            {decklistCard.card.type_line}
                          </div>
                        )}
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-600 rounded-full px-2 py-1 ml-2 flex-shrink-0">
                        {decklistCard.quantity}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Card Image Tooltip */}
      {hoveredCard && (
        <div
          className="fixed z-50 pointer-events-none"
          style={{
            left: hoverPosition.x + 10,
            top: hoverPosition.y - 10,
            transform: 'translateY(-50%)'
          }}
        >
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 p-2">
            {getCardImageUrl(hoveredCard.card) ? (
              <img
                src={getCardImageUrl(hoveredCard.card)!}
                alt={hoveredCard.card.name}
                className="w-48 h-auto rounded"
                onError={(e) => {
                  // Hide the tooltip if image fails to load
                  setHoveredCard(null);
                }}
              />
            ) : (
              <div className="w-48 h-64 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
                <span className="text-gray-500 dark:text-gray-400 text-sm">No image available</span>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
