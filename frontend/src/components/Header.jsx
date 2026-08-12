import React from 'react';

export const Header = ({ title, subtitle, onRefresh, onGenerateKey }) => {
  return (
    <header className="header">
      <div className="header-title">
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>

      <div className="header-actions">
        {onRefresh && (
          <button className="btn btn-secondary" onClick={onRefresh}>
            🔄 Refresh Data
          </button>
        )}
        {onGenerateKey && (
          <button className="btn btn-primary" onClick={onGenerateKey}>
            + New App Key
          </button>
        )}
      </div>
    </header>
  );
};
