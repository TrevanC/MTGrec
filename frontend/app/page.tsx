import DeckAnalyzer from '@/components/DeckAnalyzer';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            MTG EDH Upgrade Recommender
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Analyze your Commander deck and discover synergistic upgrades
          </p>
        </header>
        <DeckAnalyzer />
      </div>
    </main>
  );
}