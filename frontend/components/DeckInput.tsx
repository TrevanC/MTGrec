'use client';

import { useState } from 'react';

interface DeckInputProps {
  onSubmit: (decklist: string) => void;
  isLoading: boolean;
  error?: string;
  initialDecklist?: string;
}

export default function DeckInput({ onSubmit, isLoading, error, initialDecklist = '' }: DeckInputProps) {
  const [decklist, setDecklist] = useState(initialDecklist);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (decklist.trim()) {
      onSubmit(decklist.trim());
    }
  };

  const handleExampleDeck = () => {
    const exampleDecklist = `1 Prosper, Tome-Bound
1 Sol Ring
1 Arcane Signet
1 Rakdos Signet
1 Dockside Extortionist
1 Professional Face-Breaker
1 Reckless Fireweaver
1 Magda, Brazen Outlaw
1 Goldspan Dragon
1 Old Gnawbone
1 Ancient Copper Dragon
1 Chaos Warp
1 Vandalblast
1 Faithless Looting
1 Gamble
1 Jeska's Will
1 Dark Ritual
1 Cabal Ritual
1 Seething Song
1 Desperate Ritual
1 Pyretic Ritual
1 Brass's Bounty
1 Big Score
1 Bitter Reunion
1 Passionate Archaeologist
1 Tavern Scoundrel
1 Gleaming Overseer
1 Academy Manufactor
1 Kalain, Reclusive Painter
1 Junk Winder
1 Xorn
1 Hullbreacher
1 Opposition Agent
1 Spellseeker
1 Imperial Recruiter
1 Grim Tutor
1 Demonic Tutor
1 Vampiric Tutor
1 Mystical Tutor
1 Worldly Tutor
1 Enlightened Tutor
1 Rhystic Study
1 Mystic Remora
1 Phyrexian Arena
1 Necropotence
1 Underworld Breach
1 Past in Flames
1 Wheel of Fortune
1 Wheel of Misfortune
1 Windfall
1 Reforge the Soul
1 Time Spiral
1 Echo of Eons
1 Smothering Tithe
1 Dauthi Voidwalker
1 Containment Priest
1 Rest in Peace
1 Grafdigger's Cage
1 Tormod's Crypt
1 Relic of Progenitus
1 Soul-Guide Lantern
1 Command Tower
1 City of Brass
1 Mana Confluence
1 Exotic Orchard
1 Reflecting Pool
1 Forbidden Orchard
1 Gemstone Mine
1 Grand Coliseum
1 Shivan Reef
1 Underground River
1 Sulfurous Springs
1 Caves of Koilos
1 Battlefield Forge
1 Brushland
1 Llanowar Wastes
1 Karplusan Forest
1 Underground Sea
1 Volcanic Island
1 Badlands
1 Scrubland
1 Taiga
1 Savannah
1 Tropical Island
1 Tundra
1 Bayou
1 Plateau
15 Mountain
10 Swamp`;
    setDecklist(exampleDecklist);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
          Import Your Deck
        </h2>
        <p className="text-gray-600 dark:text-gray-300">
          Paste your Commander/EDH decklist below. Include your commander and all 99 cards.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="decklist" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Decklist
          </label>
          <textarea
            id="decklist"
            rows={15}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
            placeholder="1 Sol Ring&#10;1 Lightning Bolt&#10;1 Command Tower&#10;...&#10;&#10;Or paste from your favorite deckbuilding site!"
            value={decklist}
            onChange={(e) => setDecklist(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="submit"
            disabled={!decklist.trim() || isLoading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Analyzing Deck...' : 'Analyze Deck'}
          </button>

          <button
            type="button"
            onClick={handleExampleDeck}
            disabled={isLoading}
            className="bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600 disabled:opacity-50 transition-colors"
          >
            Load Example
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      <div className="mt-6 text-xs text-gray-500 dark:text-gray-400">
        <p className="mb-2">Supported formats:</p>
        <ul className="list-disc list-inside space-y-1 ml-4">
          <li>Standard format: "1 Card Name" or "1x Card Name"</li>
          <li>Moxfield, Archidekt, MTGGoldfish exports</li>
          <li>Text lists with quantities</li>
        </ul>
      </div>
    </div>
  );
}