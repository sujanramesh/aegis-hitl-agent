import { useState } from "react";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!username.trim() || !password) {
      setError(
        "Enter your username and password."
      );
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      await login(
        username.trim(),
        password
      );
    } catch (loginError) {
      setError(
        loginError.message ||
          "Unable to sign in."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-brand-panel">
        <div className="login-brand">
          <div className="brand-mark">
            <ShieldCheck
              size={22}
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

        <div className="login-brand-content">
          <span className="login-eyebrow">
            Human-in-the-loop operations
          </span>

          <h1>
            Autonomous investigation.
            <br />
            Controlled execution.
          </h1>

          <p>
            Investigate operational incidents,
            evaluate remediation risk and keep
            consequential infrastructure actions
            under explicit human authorization.
          </p>

          <div className="login-principles">
            <div>
              <CheckCircle2 size={16} />
              <span>
                Evidence-grounded reasoning
              </span>
            </div>

            <div>
              <CheckCircle2 size={16} />
              <span>
                Deterministic risk controls
              </span>
            </div>

            <div>
              <CheckCircle2 size={16} />
              <span>
                Durable human authorization
              </span>
            </div>
          </div>
        </div>

        <div className="login-system-status">
          <Activity size={15} />
          <span className="login-status-dot" />
          <span>
            Aegis control plane
          </span>
        </div>
      </section>

      <section className="login-form-panel">
        <div className="login-form-container">
          <div className="login-form-heading">
            <div className="login-lock">
              <LockKeyhole
                size={19}
                strokeWidth={1.8}
              />
            </div>

            <span>
              Secure access
            </span>

            <h2>
              Sign in to Aegis
            </h2>

            <p>
              Authenticate to access the
              operations control plane.
            </p>
          </div>

          <form
            className="login-form"
            onSubmit={handleSubmit}
          >
            <label className="form-field">
              <span>Username</span>

              <input
                type="text"
                value={username}
                onChange={(event) =>
                  setUsername(
                    event.target.value
                  )
                }
                autoComplete="username"
                placeholder="Enter username"
                disabled={isSubmitting}
                autoFocus
              />
            </label>

            <label className="form-field">
              <span>Password</span>

              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value
                  )
                }
                autoComplete="current-password"
                placeholder="Enter password"
                disabled={isSubmitting}
              />
            </label>

            {error && (
              <div
                className="login-error"
                role="alert"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              className="login-submit"
              disabled={isSubmitting}
            >
              <span>
                {isSubmitting
                  ? "Authenticating..."
                  : "Sign in"}
              </span>

              {!isSubmitting && (
                <ArrowRight
                  size={16}
                  strokeWidth={2}
                />
              )}
            </button>
          </form>

          <div className="login-security-note">
            <ShieldCheck size={14} />

            <span>
              Access is authenticated and
              authorization is enforced by
              backend RBAC policy.
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}