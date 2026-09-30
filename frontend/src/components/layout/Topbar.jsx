import { LogOut } from "lucide-react";

import { useAuth } from "../../context/AuthContext";

export default function Topbar() {
  const { user, logout } = useAuth();

  const initials =
    user?.username?.slice(0, 2).toUpperCase() || "AE";

  function formatRole(role) {
    if (!role) return "User";

    return role.charAt(0).toUpperCase() + role.slice(1);
  }

  return (
    <header className="topbar">
      <div className="topbar-context">
        <span className="topbar-context__mark" aria-hidden="true" />
        <span>AI operations control plane</span>
      </div>

      <div className="topbar-actions">
        <div className="topbar-divider" />

        <div className="profile-menu">
          <div className="avatar" aria-hidden="true">
            {initials}
          </div>

          <div className="profile-copy">
            <strong>{user?.username}</strong>
            <span>{formatRole(user?.role)}</span>
          </div>

          <button
            type="button"
            className="logout-button"
            onClick={logout}
            aria-label="Sign out"
            title="Sign out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
