import { useState, useEffect } from 'react';
import { Plus, FileText, GitCompare, BarChart3, Beaker } from 'lucide-react';
import { api } from '../api';
import type { Prompt } from '../types';

interface Props {
  selectedPromptId: string | null;
  onSelectPrompt: (prompt: Prompt) => void;
  onNewPrompt: () => void;
  onViewChange: (view: 'editor' | 'compare' | 'stats') => void;
  refreshTrigger: number;
}

export default function Sidebar({ selectedPromptId, onSelectPrompt, onNewPrompt, onViewChange, refreshTrigger }: Props) {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPrompts();
  }, [refreshTrigger]);

  const loadPrompts = async () => {
    try {
      const data = await api.listPrompts();
      setPrompts(data);
    } catch (e) {
      console.error('Failed to load prompts:', e);
    } finally {
      if (loading) setLoading(false);
    }
  };

  return (
    <aside className="w-72 bg-dark-900 border-r border-dark-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center gap-2 mb-4">
          <Beaker className="w-6 h-6 text-indigo-400" />
          <h1 className="text-lg font-bold text-white">Prompt Playground</h1>
        </div>
        <button
          onClick={onNewPrompt}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          New Prompt
        </button>
      </div>

      {/* Prompt List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {loading ? (
          <div className="text-dark-400 text-sm text-center py-8">Loading...</div>
        ) : prompts.length === 0 ? (
          <div className="text-dark-400 text-sm text-center py-8">
            No prompts yet. Create one to get started.
          </div>
        ) : (
          prompts.map((prompt) => (
            <button
              key={prompt.id}
              onClick={() => onSelectPrompt(prompt)}
              className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors group ${
                selectedPromptId === prompt.id
                  ? 'bg-dark-700 text-white'
                  : 'text-dark-300 hover:bg-dark-800 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 shrink-0 text-dark-400" />
                <span className="text-sm font-medium truncate">{prompt.name}</span>
              </div>
              {prompt.version_count > 0 && (
                <div className="ml-6 mt-0.5 text-xs text-dark-500">
                  {prompt.version_count} version{prompt.version_count !== 1 ? 's' : ''}
                </div>
              )}
            </button>
          ))
        )}
      </div>

      {/* Navigation */}
      {selectedPromptId && (
        <div className="border-t border-dark-700 p-3 space-y-1">
          <button
            onClick={() => onViewChange('editor')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-dark-300 hover:bg-dark-800 hover:text-white transition-colors text-sm"
          >
            <FileText className="w-4 h-4" />
            Editor
          </button>
          <button
            onClick={() => onViewChange('compare')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-dark-300 hover:bg-dark-800 hover:text-white transition-colors text-sm"
          >
            <GitCompare className="w-4 h-4" />
            Compare Versions
          </button>
          <button
            onClick={() => onViewChange('stats')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-dark-300 hover:bg-dark-800 hover:text-white transition-colors text-sm"
          >
            <BarChart3 className="w-4 h-4" />
            Track Improvements
          </button>
        </div>
      )}
    </aside>
  );
}
