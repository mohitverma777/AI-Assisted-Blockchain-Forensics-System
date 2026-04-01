import React from 'react';

function StatsOverview({ data }) {
    const stats = [
        { icon: '📊', value: data.totalTransactions?.toLocaleString() || '0', label: 'Transactions' },
        { icon: '💰', value: data.totalVolume || '0', label: 'Total Volume' },
        { icon: '🔗', value: data.connectedWallets || 0, label: 'Connected Wallets' },
        { icon: '⚡', value: data.balance || '0', label: 'Balance' },
        { icon: '⚠️', value: data.suspiciousActivities || 0, label: 'Suspicious' },
    ];

    return (
        <div className="stats-grid">
            {stats.map((stat, i) => (
                <div key={i} className="stat-card" style={{ animationDelay: `${i * 0.1}s` }}>
                    <div className="stat-icon">{stat.icon}</div>
                    <div className="stat-value">{stat.value}</div>
                    <div className="stat-label">{stat.label}</div>
                </div>
            ))}
        </div>
    );
}

export default StatsOverview;
