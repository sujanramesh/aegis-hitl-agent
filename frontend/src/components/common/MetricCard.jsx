import { ArrowUpRight } from "lucide-react";

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

        <ArrowUpRight
          size={14}
          strokeWidth={1.7}
          className="metric-card__icon"
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