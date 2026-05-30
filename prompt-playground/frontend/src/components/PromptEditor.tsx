import { useState, useEffect } from 'react';
import { Play, Plus, Clock, Star, ChevronDown, Loader2 } from 'lucide-react';
import { api } from '../api';
import type { Prompt, PromptVersion, RunResult } from '../types';

interface Props {
  prompt: Prompt;
}

export default function PromptEditor({ prompt }: Props) {
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<PromptVersion | null>(null);
  const [showNewVersion, setShowNewVersion] = useState(false);

  // Editor state
  const [systemPrompt, setSystemPrompt] = useState('');
  const [userPromptTemplate, setUserPromptTemplate] = useState('');
  const [model, setModel] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [notes, setNotes] = useState('');

  // Run state
  const [inputText, setInputText] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [history, setHistory] = useState<RunResult[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setVersions([]);
    setSelectedVersion(null);
    setShowNewVersion(false);
    setResult(null);
    setHistory([]);
    setInputText('');
    loadVersions();
  }, [prompt.id]);

  useEffect(() => {
    if (selectedVersion) {
      setSystemPrompt(selectedVersion.system_prompt);
      setUserPromptTemplate(selectedVersion.user_prompt_template);
      setModel(selectedVersion.model);
      setTemperature(selectedVersion.temperature);
      setNotes(selectedVersion.notes);
      loadHistory(selectedVersion.id);
    }
  }, [selectedVersion]);

  const loadVersions = async () => {
    try {
      const data = await api.listVersions(prompt.id);
      setVersions(data);
      if (data.length > 0) {
        setSelectedVersion(data[0]);
      } else {
        setShowNewVersion(true);
      }
    } catch (e) {
      console.error('Failed to load versions:', e);
    }
  };

  const loadHistory = async (versionId: string) => {
    try {
      const data = await api.getRunHistory(versionId);
      setHistory(data);
    } catch (e) {
      console.error('Failed to load history:', e);
    }
  };

  const handleSaveVersion = async () => {
    if (!userPromptTemplate.trim()) return;
    setSaving(true);
    try {
      const newVersion = await api.createVersion(prompt.id, {
        system_prompt: systemPrompt,
        user_prompt_template: userPromptTemplate,
        model,
        temperature,
        notes,
      });
      setVersions([newVersion, ...versions]);
      setSelectedVersion(newVersion);
      setShowNewVersion(false);
    } catch (e) {
      console.error('Failed to save version:', e);
    } finally {
      setSaving(false);
    }
  };

  const handleRun = async () => {
    if (!selectedVersion || !inputText.trim()) return;
    setRunning(true);
    setResult(null);
    try {
      const res = await api.runPrompt({
        version_id: selectedVersion.id,
        input_text: inputText,
        model: model || undefined,
        temperature,
      });
      setResult(res);
      setHistory([res, ...history]);
    } catch (e: any) {
      setResult({
        id: '', version_id: '', test_case_id: null, input_text: inputText,
        variables: {}, output_text: `Error: ${e.message}`, model_used: '',
        temperature: 0, latency_ms: 0, token_count: 0, rating: 0, notes: '', created_at: '',
      });
    } finally {
      setRunning(false);
    }
  };

  const handleRate = async (runId: string, rating: number) => {
    try {
      await api.rateRun(runId, { rating, notes: '' });
      setHistory(history.map((h) => (h.id === runId ? { ...h, rating } : h)));
      if (result?.id === runId) setResult({ ...result, rating });
    } catch (e) {
      console.error('Failed to rate:', e);
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-dark-900 border-b border-dark-700 px-6 py-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">{prompt.name}</h2>
          {prompt.description && <p className="text-sm text-dark-400 mt-0.5">{prompt.description}</p>}
        </div>
        <div className="flex items-center gap-3">
          {/* Version selector */}
          <div className="relative">
            <select
              value={selectedVersion?.id || ''}
              onChange={(e) => {
                const v = versions.find((v) => v.id === e.target.value);
                if (v) setSelectedVersion(v);
              }}
              className="appearance-none bg-dark-800 border border-dark-600 rounded-lg px-4 py-2 pr-8 text-sm text-white cursor-pointer"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  v{v.version_number} {v.notes ? `- ${v.notes}` : ''}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400 pointer-events-none" />
          </div>
          <button
            onClick={() => {
              setShowNewVersion(true);
              setSystemPrompt(selectedVersion?.system_prompt || '');
              setUserPromptTemplate(selectedVersion?.user_prompt_template || '');
              setNotes('');
            }}
            className="flex items-center gap-1.5 px-3 py-2 bg-dark-800 hover:bg-dark-700 border border-dark-600 rounded-lg text-sm text-dark-300 hover:text-white transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Version
          </button>
        </div>
      </header>

      {/* Main Editor Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Editor */}
        <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-4">
          {/* System Prompt */}
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1.5">System Prompt</label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="You are a helpful assistant that..."
              rows={3}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none text-sm font-mono"
            />
          </div>

          {/* User Prompt Template */}
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1.5">
              User Prompt Template
              <span className="text-dark-500 font-normal ml-2">Use {'{{input}}'} for the test input</span>
            </label>
            <textarea
              value={userPromptTemplate}
              onChange={(e) => setUserPromptTemplate(e.target.value)}
              placeholder={"Analyze the following text and provide a summary:\n\n{{input}}"}
              rows={6}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none text-sm font-mono"
            />
          </div>

          {/* Settings row */}
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Model (optional)</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="gpt-4o-mini (uses default if empty)"
                className="w-full px-4 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm"
              />
            </div>
            <div className="w-40">
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

          {/* Notes */}
          {showNewVersion && (
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Version Notes</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="What changed in this version?"
                className="w-full px-4 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm"
              />
            </div>
          )}

          {/* Save button */}
          {showNewVersion && (
            <button
              onClick={handleSaveVersion}
              disabled={!userPromptTemplate.trim() || saving}
              className="self-start px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-dark-700 disabled:text-dark-500 text-white rounded-lg transition-colors text-sm font-medium"
            >
              {saving ? 'Saving...' : `Save as v${(versions[0]?.version_number || 0) + 1}`}
            </button>
          )}

          {/* Test Input */}
          <div className="border-t border-dark-700 pt-4">
            <label className="block text-sm font-medium text-dark-300 mb-1.5">Test Input</label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter your test input here..."
              rows={4}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-dark-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none text-sm"
            />
            <button
              onClick={handleRun}
              disabled={!selectedVersion || !inputText.trim() || running}
              className="mt-3 flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-dark-700 disabled:text-dark-500 text-white rounded-lg transition-colors text-sm font-medium"
            >
              {running ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Prompt
                </>
              )}
            </button>
          </div>

          {/* Output */}
          {result && (
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white">Output</h3>
                <div className="flex items-center gap-3 text-xs text-dark-400">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {result.latency_ms}ms
                  </span>
                  {result.token_count > 0 && <span>{result.token_count} tokens</span>}
                  <span className="text-dark-500">{result.model_used}</span>
                </div>
              </div>
              <div className="text-sm text-dark-200 whitespace-pre-wrap leading-relaxed">
                {result.output_text}
              </div>
              {/* Rating */}
              {result.id && (
                <div className="mt-4 pt-3 border-t border-dark-700 flex items-center gap-2">
                  <span className="text-xs text-dark-400">Rate:</span>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => handleRate(result.id, star)}
                      className="transition-colors"
                    >
                      <Star
                        className={`w-4 h-4 ${
                          star <= result.rating ? 'text-yellow-400 fill-yellow-400' : 'text-dark-600'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: History */}
        <div className="w-80 border-l border-dark-700 bg-dark-900 overflow-y-auto">
          <div className="p-4 border-b border-dark-700">
            <h3 className="text-sm font-semibold text-white">Run History</h3>
          </div>
          <div className="p-3 space-y-2">
            {history.length === 0 ? (
              <p className="text-xs text-dark-500 text-center py-4">No runs yet</p>
            ) : (
              history.map((run) => (
                <div
                  key={run.id}
                  className="bg-dark-800 rounded-lg p-3 border border-dark-700 hover:border-dark-600 cursor-pointer transition-colors"
                  onClick={() => {
                    setInputText(run.input_text);
                    setResult(run);
                  }}
                >
                  <div className="text-xs text-dark-400 truncate mb-1">{run.input_text}</div>
                  <div className="text-xs text-dark-300 line-clamp-2">{run.output_text}</div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-1">
                      {run.rating > 0 && (
                        <div className="flex items-center gap-0.5">
                          <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                          <span className="text-xs text-dark-400">{run.rating}</span>
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-dark-500">{run.latency_ms}ms</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
