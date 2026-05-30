import { useState } from 'react';
import Sidebar from './components/Sidebar';
import PromptEditor from './components/PromptEditor';
import CompareView from './components/CompareView';
import StatsView from './components/StatsView';
import WelcomeScreen from './components/WelcomeScreen';
import type { Prompt } from './types';

type View = 'welcome' | 'editor' | 'compare' | 'stats';

export default function App() {
  const [currentView, setCurrentView] = useState<View>('welcome');
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);

  const handleSelectPrompt = (prompt: Prompt) => {
    setSelectedPrompt(prompt);
    setCurrentView('editor');
  };

  const handleNewPrompt = () => {
    setSelectedPrompt(null);
    setCurrentView('welcome');
  };

  const handlePromptCreated = (prompt: Prompt) => {
    setSidebarRefresh((n) => n + 1);
    // Small delay to let sidebar update before switching view
    setTimeout(() => {
      setSelectedPrompt(prompt);
      setCurrentView('editor');
    }, 100);
  };

  return (
    <div className="flex h-screen bg-dark-950">
      <Sidebar
        selectedPromptId={selectedPrompt?.id || null}
        onSelectPrompt={handleSelectPrompt}
        onNewPrompt={handleNewPrompt}
        onViewChange={setCurrentView}
        refreshTrigger={sidebarRefresh}
      />
      <main className="flex-1 flex flex-col overflow-hidden">
        {currentView === 'welcome' && (
          <WelcomeScreen onPromptCreated={handlePromptCreated} />
        )}
        {currentView === 'editor' && selectedPrompt && (
          <PromptEditor prompt={selectedPrompt} />
        )}
        {currentView === 'compare' && selectedPrompt && (
          <CompareView prompt={selectedPrompt} />
        )}
        {currentView === 'stats' && selectedPrompt && (
          <StatsView prompt={selectedPrompt} />
        )}
      </main>
    </div>
  );
}
