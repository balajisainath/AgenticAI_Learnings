import { useState, useEffect } from 'react';
import { Play, Loader2, Clock, Hash } from 'lucide-react';
import { api } from '../api';
import type { Prompt, PromptVersion, CompareResult } from '../types';

interface Props {
  prompt: Prompt;
}

export default function CompareView({ prompt }: Props) {
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [inputText, setInputText] = useState('');
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<CompareResult[]>([]);
  const [model, setModel] = useState('');
  const [temperature, setTemperature] = useState(0.7);

  useEffect(() => {
    loadVersions();
  }, [prompt.id]);

  const loadVersions = async () => {
    try {
      const data = await api.listVersions(prompt.id);
      setVersions(data);
      // Pre-select first two versions
      if (data.length >= 2) {
        setSelectedVersions([data[0].id, data[1].id]);
      } else if (data.length === 1) {
        setSelectedVersions([data[0].id]);
      }
    } catch (e) {
      console.error('Failed to load versions:', e);
    }
  };

  const toggleVersion = (id: string) => {
    setSelectedVersions((prev) =>
      prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]
    );
  };

  const handleCompare = async () => {
    if (selectedVersions.length < 2 || !inputText.trim()) return;
    setRunning(true);
    setResults([]);
    try {
      const response = await api.compare({
        prompt_id: prompt.id,
        version_ids: selectedVersions,
        input_text: inputText,
        model: model || undefined,
        temperature,
      });
      setResults(response.results);
    } catch (e: any) {
      console.error('Compare failed:', e);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-dark-900 border-b border-dark-700 px-6 py-4">
        <h2 className="text-xl font-bold text-white">Compare Versions</h2>
        <p className="text-sm text-dark-400 mt-0.5">
          Run the same input against multiple prompt versions side-by-side
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Version Selection */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            Select versions to compare (minimum 2)
          </label>
          <div className="flex flex-wrap gap-2">
            {versions.map((v) => (
              <button
                key={v.id}
                onClick={() => toggleVersion(v.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
                  selectedVersions.includes(v.id)
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-dark-800 border-dark-600 text-dark-300 hover:border-dark-500'
                }`}
              >
                v{v.version_number}
                {v.notes && <span className="ml-1 text-xs opacity-70">({v.notes})</span>}
              </button>
            ))}
          </div>
          {versions.length < 2 && (
            <p className="text-xs text-amber-400 mt-2">
              You need at least 2 versions to compare. Create more versions in the Editor.
            </p>
          )}
        </div>

        {/* Settings */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-dark-300 mb-1.5">Model Override (optional)</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="Uses each version's model if empty"
              className="w-full px-4 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm"
            />
          </div>
          <div className="w-48">
            <label className="block text-sm font-medium text-dark-300 mb-1.5">Temperature: {temperature}</label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full mt-2 accent-indigo-500"
            />
          </div>
        </div>

        {/* Input */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-1.5">Test Input</label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Enter the same input to test against all selected versions..."
            rows={4}
            className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none text-sm"
          />
          <button
            onClick={handleCompare}
            disabled={selectedVersions.length < 2 || !inputText.trim() || running}
            className="mt-3 flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-dark-700 disabled:text-dark-500 text-white rounded-lg transition-colors text-sm font-medium"
          >
            {running ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Comparing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Compare ({selectedVersions.length} versions)
              </>
            )}
          </button>
        </div>

        {/* Results Grid */}
        {results.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Comparison Results</h3>
            <div className={`grid gap-4 ${results.length === 2 ? 'grid-cols-2' : results.length === 3 ? 'grid-cols-3' : 'grid-cols-2'}`}>
              {results.map((r) => (
                <div key={r.version_id} className="bg-dark-800 border border-dark-600 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3 pb-2 border-b border-dark-700">
                    <span className="text-sm font-bold text-indigo-400">v{r.version_number}</span>
                    <div className="flex items-center gap-3 text-xs text-dark-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {r.latency_ms}ms
                      </span>
                      {r.token_count > 0 && (
                        <span className="flex items-center gap-1">
                          <Hash className="w-3 h-3" />
                          {r.token_count}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-dark-200 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
                    {r.output_text}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
