import { AlertCircle, LoaderCircle, X } from "lucide-react";
import { useState } from "react";

import { createIncident } from "../../services/api.js";

export default function NewIncidentModal({
  open,
  onClose,
  onCreated,
}) {
  const [title, setTitle] = useState("");
  const [service, setService] = useState("");
  const [description, setDescription] = useState("");

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  if (!open) {
    return null;
  }

  function resetForm() {
    setTitle("");
    setService("");
    setDescription("");
    setError("");
  }

  function handleClose() {
    if (isSubmitting) {
      return;
    }

    resetForm();
    onClose();
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const cleanTitle = title.trim();
    const cleanService = service.trim();
    const cleanDescription = description.trim();

    if (
      !cleanTitle ||
      !cleanService ||
      !cleanDescription
    ) {
      setError(
        "Complete all incident fields before starting the investigation."
      );
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      const incident = await createIncident({
        title: cleanTitle,
        service: cleanService,
        description: cleanDescription,
      });

      resetForm();

      if (onCreated) {
        onCreated(incident);
      }

      onClose();
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to create the incident."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          handleClose();
        }
      }}
    >
      <section
        className="incident-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-incident-title"
      >
        <div className="incident-modal__header">
          <div>
            <span className="eyebrow">
              Incident intake
            </span>

            <h2 id="new-incident-title">
              Start investigation
            </h2>

            <p>
              Provide the operational context Aegis
              should investigate.
            </p>
          </div>

          <button
            type="button"
            className="incident-modal__close"
            onClick={handleClose}
            disabled={isSubmitting}
            aria-label="Close incident form"
          >
            <X size={18} />
          </button>
        </div>

        <form
          className="incident-form"
          onSubmit={handleSubmit}
        >
          <label className="form-field">
            <span>Incident title</span>

            <input
              type="text"
              value={title}
              onChange={(event) =>
                setTitle(event.target.value)
              }
              placeholder="Payment failures after deployment"
              minLength={3}
              maxLength={200}
              disabled={isSubmitting}
              autoFocus
              required
            />
          </label>

          <label className="form-field">
            <span>Affected service</span>

            <input
              type="text"
              value={service}
              onChange={(event) =>
                setService(event.target.value)
              }
              placeholder="payment-service"
              minLength={2}
              maxLength={100}
              disabled={isSubmitting}
              required
            />
          </label>

          <label className="form-field">
            <span>Description</span>

            <textarea
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              placeholder="Describe the observed symptoms, impact and any relevant operational context."
              minLength={10}
              maxLength={2000}
              rows={6}
              disabled={isSubmitting}
              required
            />

            <small className="field-hint">
              {description.length} / 2000
            </small>
          </label>

          {error && (
            <div
              className="incident-form__error"
              role="alert"
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="incident-modal__actions">
            <button
              type="button"
              className="button"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="button button--primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <LoaderCircle
                    size={15}
                    className="spinner"
                  />
                  Investigating...
                </>
              ) : (
                "Start investigation"
              )}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}