export default function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
}) {
  return (
    <article className="metric-card">
      <div className="metric-card__header">
        <span>{label}</span>

        <span
          className={`metric-card__indicator metric-card__indicator--${tone}`}
          aria-hidden="true"
        />
      </div>

      <div className={`metric-card__value metric-card__value--${tone}`}>
        {value}
      </div>

      <div className="metric-card__detail">
        {detail}
      </div>
    </article>
  );
}
