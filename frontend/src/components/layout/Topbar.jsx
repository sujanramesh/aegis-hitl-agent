import {
    Bell,
    ChevronDown,
    CircleCheck,
    LogOut,
  } from "lucide-react";
  
  import { useAuth } from "../../context/AuthContext";
  
  export default function Topbar() {
    const {
      user,
      logout,
    } = useAuth();
  
    const initials =
      user?.username
        ?.slice(0, 2)
        .toUpperCase() || "AE";
  
    function formatRole(role) {
      if (!role) {
        return "User";
      }
  
      return (
        role.charAt(0).toUpperCase() +
        role.slice(1)
      );
    }
  
    return (
      <header className="topbar">
        <div className="system-health">
          <CircleCheck
            size={16}
            strokeWidth={2}
          />
          <span>
            Systems operational
          </span>
        </div>
  
        <div className="topbar-actions">
          <button
            type="button"
            className="icon-button"
            aria-label="Notifications"
          >
            <Bell size={18} />
            <span className="notification-dot" />
          </button>
  
          <div className="topbar-divider" />
  
          <div className="profile-menu">
            <div className="avatar">
              {initials}
            </div>
  
            <div className="profile-copy">
              <strong>
                {user?.username}
              </strong>
  
              <span>
                {formatRole(user?.role)}
              </span>
            </div>
  
            <ChevronDown
              size={15}
              className="profile-chevron"
            />
  
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