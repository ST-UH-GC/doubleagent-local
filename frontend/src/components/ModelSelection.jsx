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
        <option value="qwen3:14b">Qwen 3 14B</option>
      </select>
    </label>
  );
};

export default ModelSelection;
