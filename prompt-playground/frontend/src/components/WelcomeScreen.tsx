import { useState } from 'react';
import { Sparkles, Zap } from 'lucide-react';
import { api } from '../api';
import type { Prompt } from '../types';

interface Props {
  onPromptCreated: (prompt: Prompt) => void;
}

export default function WelcomeScreen({ onPromptCreated }: Props) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      const prompt = await api.createPrompt({ name: name.trim(), description: description.trim() });
      onPromptCreated(prompt);
    } catch (e) {
      console.error('Failed to create prompt:', e);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-2xl w-full text-center">
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Sparkles className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-3">Prompt Testing Playground</h2>
          <p className="text-dark-400 text-lg max-w-md mx-auto">
            Compare prompt versions side-by-side, track improvements, and iterate faster on your LLM prompts.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-3 gap-4 mb-10">
          <div className="bg-dark-900 rounded-xl p-4 border border-dark-700">
            <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-indigo-500/10 flex items-center justify-center">
              <Zap className="w-5 h-5 text-indigo-400" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Version Control</h3>
            <p className="text-xs text-dark-400">Store v1, v2, v3... of your prompts with full history</p>
          </div>
          <div className="bg-dark-900 rounded-xl p-4 border border-dark-700">
            <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-purple-400" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Compare Outputs</h3>
            <p className="text-xs text-dark-400">Run same input against multiple versions side-by-side</p>
          </div>
          <div className="bg-dark-900 rounded-xl p-4 border border-dark-700">
            <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <Zap className="w-5 h-5 text-emerald-400" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Track Quality</h3>
            <p className="text-xs text-dark-400">Rate outputs, measure latency, and track improvements</p>
          </div>
        </div>

        {/* Create Form */}
        {!showForm ? (
          <button
            onClick={() => setShowForm(true)}
            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-colors font-medium text-lg"
          >
            Create Your First Prompt
          </button>
        ) : (
          <div className="bg-dark-900 rounded-xl p-6 border border-dark-700 text-left">
            <h3 className="text-lg font-semibold text-white mb-4">Create New Prompt</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Email Writer, Code Reviewer, Summarizer..."
                  className="w-full px-4 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5">Description (optional)</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What does this prompt do?"
                  className="w-full px-4 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCreate}
                  disabled={!name.trim() || creating}
                  className="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-dark-700 disabled:text-dark-500 text-white rounded-lg transition-colors font-medium"
                >
                  {creating ? 'Creating...' : 'Create Prompt'}
                </button>
                <button
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2.5 bg-dark-800 hover:bg-dark-700 text-dark-300 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
