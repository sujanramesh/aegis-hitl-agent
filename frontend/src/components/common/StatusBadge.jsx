export default function StatusBadge({ status, children }) {
    const normalized = status?.toLowerCase() || "neutral";
  
    return (
      <span className={`status-badge status-badge--${normalized}`}>
        <span className="status-badge__dot" />
        {children || status}
      </span>
    );
  }