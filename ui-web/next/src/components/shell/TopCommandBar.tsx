"use client";

type TopCommandBarProps = {
  activeLabel: string;
};

export function TopCommandBar({ activeLabel }: TopCommandBarProps) {
  return (
    <header className="sf-topbar">
      <div className="sf-search">
        <span className="sf-search-icon">⌕</span>
        <input
          className="sf-search-input"
          placeholder={`Search ${activeLabel}`}
          aria-label="Search"
        />
      </div>
      <div className="sf-top-actions">
        <button className="sf-icon-btn" type="button" aria-label="Theme">
          ◐
        </button>
        <button className="sf-icon-btn" type="button" aria-label="Notifications">
          ◔
        </button>
        <button className="sf-icon-btn" type="button" aria-label="Profile">
          ●
        </button>
      </div>
    </header>
  );
}
