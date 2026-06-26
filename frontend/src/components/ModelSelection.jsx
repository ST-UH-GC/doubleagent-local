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
        <option value="llama3.2">Llama 3.2 (fast)</option>
        <option value="llama3.1">Llama 3.1</option>
        <option value="mistral">Mistral</option>
        <option value="gemma3">Gemma 3</option>
      </select>
    </label>
  );
};

export default ModelSelection;
