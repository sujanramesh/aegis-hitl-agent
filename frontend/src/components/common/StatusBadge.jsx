export default function StatusBadge({ status, children }) {
    const normalized = status?.toLowerCase() || "neutral";
  
    return (
      <span
        className={`status-badge status-badge--${normalized}`}
        role="status"
      >
        <span className="status-badge__dot" aria-hidden="true" />
        {children || status}
      </span>
    );
  }
