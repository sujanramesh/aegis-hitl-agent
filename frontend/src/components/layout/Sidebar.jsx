import {
  Activity,
  BellRing,
  FileClock,
  Gauge,
  Layers3,
  ServerCog,
  ShieldCheck,
} from "lucide-react";

const primaryNavigation = [
  {
    id: "overview",
    label: "Overview",
    icon: Gauge,
  },
  {
    id: "incidents",
    label: "Incidents",
    icon: Activity,
  },
  {
    id: "approvals",
    label: "Approvals",
    icon: BellRing,
  },
  {
    id: "services",
    label: "Services",
    icon: ServerCog,
  },
];

const observeNavigation = [
  {
    id: "observability",
    label: "Observability",
    icon: Layers3,
  },
  {
    id: "audit",
    label: "Audit trail",
    icon: FileClock,
  },
];

function NavigationItem({
  item,
  active,
  onSelect,
}) {
  const Icon = item.icon;

  return (
    <button
      type="button"
      className={`nav-item ${
        active ? "nav-item--active" : ""
      }`}
      onClick={() => onSelect(item.id)}
    >
      <Icon size={17} strokeWidth={1.8} />

      <span>{item.label}</span>

      {item.badge && (
        <span className="nav-badge">
          {item.badge}
        </span>
      )}
    </button>
  );
}

export default function Sidebar({
  activePage,
  onNavigate,
}) {
  const environmentLabel =
    import.meta.env.VITE_APP_ENV || "Local";

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <ShieldCheck
            size={20}
            strokeWidth={1.9}
          />
        </div>

        <div className="brand-copy">
          <div className="brand-name">
            AEGIS
          </div>

          <div className="brand-description">
            Autonomous Operations
          </div>
        </div>
      </div>

      <nav
        className="navigation"
        aria-label="Primary navigation"
      >
        <div className="nav-group">
          {primaryNavigation.map(
            (item) => (
              <NavigationItem
                key={item.id}
                item={item}
                active={
                  activePage === item.id
                }
                onSelect={onNavigate}
              />
            )
          )}
        </div>

        <div className="nav-section-label">
          Observe
        </div>

        <div className="nav-group">
          {observeNavigation.map(
            (item) => (
              <NavigationItem
                key={item.id}
                item={item}
                active={
                  activePage === item.id
                }
                onSelect={onNavigate}
              />
            )
          )}
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="environment">
          <span className="environment-dot" />

          <div>
            <span className="environment-label">
              Environment
            </span>

            <strong>
              {environmentLabel}
            </strong>
          </div>
        </div>
      </div>
    </aside>
  );
}