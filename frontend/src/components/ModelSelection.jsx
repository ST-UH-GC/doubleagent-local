const MODELS = {
  ollama: [{ value: 'qwen3:14b', label: 'Qwen 3 14B' }],
  anthropic: [
    { value: 'claude-sonnet-4-5', label: 'Claude Sonnet (recommended)' },
    { value: 'claude-haiku-4-5', label: 'Claude Haiku (fast)' },
    { value: 'claude-opus-4-5', label: 'Claude Opus (powerful)' },
  ],
};

const provider = import.meta.env.VITE_PROVIDER || 'ollama';
const models = MODELS[provider] ?? MODELS.ollama;

const ModelSelection = ({ selectedModel, setSelectedModel }) => {
  return (
    <label className="select form-control">
      <span className="label">Model:</span>

      <select
        id="model-select"
        value={selectedModel}
        onChange={(e) => setSelectedModel(e.target.value)}
        className="select select-bordered"
      >
        {models.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  );
};

export default ModelSelection;
