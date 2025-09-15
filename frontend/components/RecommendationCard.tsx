'use client';

import Image from 'next/image';
import { Recommendation } from '@/lib/types';
import { getCardImageUrl, getCardPrice, formatPrice } from '@/lib/scryfall';
import { api } from '@/lib/api';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export default function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const { card, score, explanation } = recommendation;

  const imageUrl = getCardImageUrl(card, 'normal');
  const price = getCardPrice(card);

  const handleCardClick = async () => {
    try {
      await api.submitFeedback(card.id, 'clicked');
    } catch (error) {
      console.warn('Failed to submit feedback:', error);
    }
  };

  const handleAddCard = async () => {
    try {
      await api.submitFeedback(card.id, 'added');
      // Here you would typically update the deck state
      // For now, just show a success message
      alert(`Added ${card.name} to your consideration list!`);
    } catch (error) {
      console.warn('Failed to submit feedback:', error);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 dark:border-gray-700">
      {/* Card Header */}
      <div className="p-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 dark:text-white truncate">
              {card.name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 truncate">
              {card.type_line}
            </p>
          </div>
          <div className="ml-2 flex-shrink-0">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {score}
            </span>
          </div>
        </div>
      </div>

      {/* Card Image */}
      <div className="relative h-48 bg-gray-100 dark:bg-gray-700">
        {imageUrl ? (
          <Image
            src={imageUrl}
            alt={card.name}
            fill
            className="object-contain cursor-pointer"
            onClick={handleCardClick}
            onError={(e) => {
              // Hide broken images
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="h-full flex items-center justify-center">
            <span className="text-gray-500 dark:text-gray-400 text-sm">
              No image available
            </span>
          </div>
        )}
      </div>

      {/* Card Details */}
      <div className="p-4">
        {/* Price */}
        {price > 0 && (
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-600 dark:text-gray-300">Price:</span>
            <span className={`font-semibold ${
              price < 5 ? 'text-green-600 dark:text-green-400' :
              price < 25 ? 'text-yellow-600 dark:text-yellow-400' :
              'text-red-600 dark:text-red-400'
            }`}>
              {formatPrice(price)}
            </span>
          </div>
        )}

        {/* Explanation */}
        <div className="mb-4">
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
            {explanation.summary}
          </p>

          {explanation.reasons && explanation.reasons.length > 0 && (
            <div className="space-y-1">
              {explanation.reasons.slice(0, 2).map((reason, index) => (
                <div key={index} className="flex items-center text-xs text-gray-600 dark:text-gray-400">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 flex-shrink-0"></span>
                  <span className="flex-1">{reason.detail}</span>
                  <span className="ml-2 font-medium">{Math.round(reason.weight * 100)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex space-x-2">
          <button
            onClick={handleAddCard}
            className="flex-1 bg-blue-600 text-white text-sm font-medium px-3 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Consider
          </button>
          <button className="px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 transition-colors">
            Hide
          </button>
        </div>
      </div>

      {/* Oracle Text (expandable) */}
      {card.oracle_text && (
        <div className="px-4 pb-4">
          <details className="text-xs">
            <summary className="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
              Card Text
            </summary>
            <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-700 rounded text-gray-700 dark:text-gray-300 text-xs">
              {card.oracle_text}
            </div>
          </details>
        </div>
      )}
    </div>
  );
}