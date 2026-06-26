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
        <option value="llama3.2">Llama 3.2</option>
        <option value="qwen3:8b">Qwen 3 8B</option>
        <option value="mistral">Mistral</option>
      </select>
    </label>
  );
};

export default ModelSelection;
