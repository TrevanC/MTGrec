'use client';

import { useState } from 'react';

interface DeckInputProps {
  onSubmit: (commander1: string, commander2: string, decklist: string) => void;
  isLoading: boolean;
  error?: string;
  initialCommander1?: string;
  initialCommander2?: string;
  initialDecklist?: string;
}

export default function DeckInput({ onSubmit, isLoading, error, initialCommander1 = '', initialCommander2 = '', initialDecklist = '' }: DeckInputProps) {
  const [commander1, setCommander1] = useState(initialCommander1);
  const [commander2, setCommander2] = useState(initialCommander2);
  const [decklist, setDecklist] = useState(initialDecklist);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (commander1.trim() && decklist.trim()) {
      onSubmit(commander1.trim(), commander2.trim(), decklist.trim());
    }
  };

  const handleExampleDeck = () => {
    const exampleCommander1 = 'Hearthhull, the Worldseed';
    const exampleCommander2 = '';
    const exampleDecklist = `1 Szarel, Genesis Shepherd (EOC) 4
1 Aftermath Analyst (EOC) 91
1 Arcane Signet (EOC) 53
1 Augur of Autumn (EOC) 92
1 Baloth Prime (EOC) 13
1 Beast Within (EOC) 93
1 Binding the Old Gods (EOC) 52
1 Blasphemous Act (EOC) 86
1 Bojuka Bog (EOC) 149
1 Braids, Arisen Nightmare (EOC) 82
1 Cabaretti Courtyard (EOC) 151
1 Canyon Slough (EOC) 152
1 Centaur Vinecrasher (EOC) 94
1 Cinder Glade (EOC) 154
1 Command Tower (EOC) 59
1 Cultivate (EOC) 95
1 Dakmor Salvage (EOC) 156
1 Escape to the Wilds (EOC) 115
1 Escape Tunnel (EOC) 157
1 Eumidian Hatchery (EOC) 20
1 Eumidian Wastewaker (EOC) 8
1 Evendo Brushrazer (EOC) 10
1 Evolving Wilds (EOC) 158
1 Exploration Broodship (EOC) 14
1 Fabled Passage (EOC) 60
1 Farseek (EOC) 50
1 Festering Thicket (EOC) 21
4 Forest (EOE) 276
4 Forest (EOE) 275
1 Formless Genesis (EOC) 96
1 Gaze of Granite (EOC) 116
1 God-Eternal Bontu (EOC) 83
1 Groundskeeper (EOC) 97
1 Hammer of Purphoros (EOC) 88
1 Harrow (EOC) 98
1 Horizon Explorer (EOC) 15
1 Infernal Grasp (EOC) 84
1 Juri, Master of the Revue (EOC) 119
1 Karplusan Forest (EOC) 164
1 Korvold, Fae-Cursed King (EOC) 120
1 Llanowar Wastes (EOC) 165
1 Loamcrafter Faun (EOC) 99
1 Maestros Theater (EOC) 167
1 Mayhem Devil (EOC) 121
1 Mazirek, Kraul Death Priest (EOC) 122
1 Moraug, Fury of Akoum (EOC) 89
1 Mountain (EOE) 274
2 Mountain (EOE) 273
1 Mountain Valley (EOC) 61
1 Multani, Yavimaya's Avatar (EOC) 100
1 Myriad Landscape (EOC) 169
1 Nature's Lore (EOC) 101
1 Night's Whisper (EOC) 85
1 Omnath, Locus of Rage (EOC) 123
1 Oracle of Mul Daya (EOC) 102
1 Pest Infestation (EOC) 103
1 Planetary Annihilation (EOC) 12
1 Putrefy (EOC) 124
1 Rakdos Charm (EOC) 125
1 Rampaging Baloths (EOC) 104
1 Riveteers Overlook (EOC) 172
1 Rocky Tar Pit (EOC) 173
1 Roiling Regrowth (EOC) 105
1 Satyr Wayfinder (EOC) 106
1 Scouring Swarm (EOC) 16
1 Sheltered Thicket (EOC) 178
1 Skyshroud Claim (EOC) 107
1 Smoldering Marsh (EOC) 182
1 Sol Ring (EOC) 57
1 Soul of Windgrace (EOC) 126
1 Splendid Reclamation (EOC) 108
1 Springbloom Druid (EOC) 51
1 Sprouting Goblin (EOC) 90
1 Sulfurous Springs (EOC) 185
3 Swamp (EOE) 271
2 Swamp (EOE) 272
1 Tear Asunder (EOC) 109
1 Terramorphic Expanse (EOC) 62
1 The Gitrog Monster (EOC) 117
1 Tireless Tracker (EOC) 110
1 Titania, Protector of Argoth (EOC) 111
1 Twilight Mire (EOC) 189
1 Uurg, Spawn of Turg (EOC) 127
1 Vernal Fen (EOC) 24
1 Viridescent Bog (EOC) 190
1 Wastes (EOC) 191
1 Windgrace's Judgment (EOC) 129
1 World Breaker (EOC) 112
1 Worldsoul's Rage (EOC) 130`;
    setCommander1(exampleCommander1);
    setCommander2(exampleCommander2);
    setDecklist(exampleDecklist);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
          Import Your Deck
        </h2>
        <p className="text-gray-600 dark:text-gray-300">
          Enter your commander(s) and paste your Commander/EDH decklist below. For partner commanders, enter both. The decklist should contain 99 cards (single commander) or 98 cards (partner commanders).
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="commander1" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Commander 1
            </label>
            <input
              id="commander1"
              type="text"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="e.g., Hearthhull, the Worldseed"
              value={commander1}
              onChange={(e) => setCommander1(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div>
            <label htmlFor="commander2" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Commander 2 (Optional - Partner)
            </label>
            <input
              id="commander2"
              type="text"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="e.g., Szarel, Genesis Shepherd (optional)"
              value={commander2}
              onChange={(e) => setCommander2(e.target.value)}
              disabled={isLoading}
            />
          </div>
        </div>

        <div>
          <label htmlFor="decklist" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Decklist ({commander2.trim() ? '98' : '99'} cards)
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
            disabled={!commander1.trim() || !decklist.trim() || isLoading}
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