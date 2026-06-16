export default function ProgressPanel({ steps }) {
    return (
      <div className="progress-panel">
        <div className="progress-title">Execution trace</div>
  
        {steps.length === 0 ? (
          <div className="progress-empty">
            Ask a question to see the agent workflow.
          </div>
        ) : (
          steps.map((step, index) => (
            <div key={index} className="progress-step">
              <span className="progress-dot"></span>
              <span>{step}</span>
            </div>
          ))
        )}
      </div>
    );
  }