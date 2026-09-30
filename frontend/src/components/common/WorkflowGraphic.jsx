const steps = [
  { label: "Incident", tone: "" },
  { label: "Evidence", tone: "" },
  { label: "AI investigation", tone: "ai" },
  { label: "Risk policy", tone: "" },
  { label: "Human approval", tone: "human" },
  { label: "Execution", tone: "" },
  { label: "Recovery", tone: "" },
];

export default function WorkflowGraphic() {
  return (
    <section className="workflow-graphic" aria-label="Aegis product workflow illustration">
      <div className="workflow-graphic__heading">
        <strong>Aegis control path</strong>
        <span>Illustrative product workflow · not live incident status</span>
      </div>

      <ol className="workflow-graphic__steps">
        {steps.map((step, index) => (
          <li
            className={`workflow-graphic__step${step.tone ? ` workflow-graphic__step--${step.tone}` : ""}`}
            key={step.label}
          >
            <span className="workflow-graphic__node" aria-hidden="true">{index + 1}</span>
            <span className="workflow-graphic__label">{step.label}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
