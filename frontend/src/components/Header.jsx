import React from 'react';

function Header({ currentPage, onNavigate }) {
    const pages = [
        { id: 'dashboard', label: 'Dashboard', icon: '🔍' },
    ];

    return (
        <header className="header">
            <div className="header-inner">
                <div className="header-brand">
                    <span className="header-logo">🔗</span>
                    <div>
                        <div className="header-title">Blockchain Forensics</div>
                        <div className="header-subtitle">AI-Assisted Analysis System</div>
                    </div>
                </div>
                <nav className="header-nav">
                    {pages.map(page => (
                        <button
                            key={page.id}
                            className={`nav-btn ${currentPage === page.id ? 'active' : ''}`}
                            onClick={() => onNavigate(page.id)}
                        >
                            {page.icon} {page.label}
                        </button>
                    ))}
                </nav>
            </div>
        </header>
    );
}

export default Header;
