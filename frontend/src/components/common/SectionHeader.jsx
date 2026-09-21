export default function SectionHeader({ eyebrow, title, action }) {
    return (
      <div className="section-header">
        <div>
          {eyebrow && (
            <span className="section-header__eyebrow">
              {eyebrow}
            </span>
          )}
  
          <h2>{title}</h2>
        </div>
  
        {action && (
          <div className="section-header__action">
            {action}
          </div>
        )}
      </div>
    );
  }