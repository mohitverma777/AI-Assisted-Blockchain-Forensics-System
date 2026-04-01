import React, { useState } from 'react';

const PAGE_SIZE = 50;

function TransactionList({ transactions = [] }) {
    const [filter, setFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);

    const filtered = transactions.filter(tx => {
        if (filter !== 'all' && tx.type?.toLowerCase() !== filter) return false;
        if (searchTerm && !tx.hash?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
        return true;
    });

    // Pagination
    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    const safeCurrentPage = Math.min(currentPage, totalPages);
    const startIdx = (safeCurrentPage - 1) * PAGE_SIZE;
    const pageItems = filtered.slice(startIdx, startIdx + PAGE_SIZE);

    // Reset to page 1 when filter/search changes
    const handleFilterChange = (f) => {
        setFilter(f);
        setCurrentPage(1);
    };

    const handleSearchChange = (e) => {
        setSearchTerm(e.target.value);
        setCurrentPage(1);
    };

    const formatDate = (ts) => {
        try {
            const d = new Date(ts);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                + ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        } catch {
            return ts;
        }
    };

    // Generate pagination range with ellipsis
    const getPageRange = () => {
        const pages = [];
        if (totalPages <= 7) {
            for (let i = 1; i <= totalPages; i++) pages.push(i);
        } else {
            pages.push(1);
            if (safeCurrentPage > 3) pages.push('...');
            for (let i = Math.max(2, safeCurrentPage - 1); i <= Math.min(totalPages - 1, safeCurrentPage + 1); i++) {
                pages.push(i);
            }
            if (safeCurrentPage < totalPages - 2) pages.push('...');
            pages.push(totalPages);
        }
        return pages;
    };

    return (
        <div className="card" style={{ gridColumn: '1 / -1' }}>
            <div className="card-header">
                <div className="card-title"><span className="icon">📜</span> Transaction History</div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                        type="text"
                        placeholder="Search hash..."
                        value={searchTerm}
                        onChange={handleSearchChange}
                        style={{
                            background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                            borderRadius: '6px', padding: '6px 12px', fontSize: '12px',
                            color: 'var(--text-primary)', fontFamily: 'var(--font-mono)',
                            outline: 'none', width: '180px'
                        }}
                    />
                    {['all', 'sent', 'received'].map(f => (
                        <button key={f} onClick={() => handleFilterChange(f)} style={{
                            background: filter === f ? 'var(--accent-glow)' : 'transparent',
                            border: `1px solid ${filter === f ? 'var(--accent)' : 'var(--border)'}`,
                            borderRadius: '6px', padding: '5px 12px', fontSize: '11px',
                            color: filter === f ? 'var(--accent)' : 'var(--text-muted)',
                            cursor: 'pointer', fontFamily: 'var(--font-sans)', fontWeight: '500',
                            textTransform: 'capitalize'
                        }}>
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {filtered.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px 0', fontSize: '14px' }}>
                    No transactions found.
                </p>
            ) : (
                <div style={{ overflowX: 'auto' }}>
                    <table className="transactions-table">
                        <thead>
                            <tr>
                                <th>Hash</th>
                                <th>Type</th>
                                <th>Amount</th>
                                <th>From</th>
                                <th>To</th>
                                <th>Time</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {pageItems.map(tx => (
                                <tr key={tx.id}>
                                    <td>
                                        <span className="tx-hash">
                                            {tx.hash?.length > 18 ? `${tx.hash.slice(0, 8)}...${tx.hash.slice(-6)}` : tx.hash}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`tx-type ${tx.type?.toLowerCase()}`}>
                                            {tx.type === 'Sent' ? '↑ Sent' : tx.type === 'Received' ? '↓ Recv' : tx.type}
                                        </span>
                                    </td>
                                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>{tx.amount}</td>
                                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>{tx.from}</td>
                                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>{tx.to}</td>
                                    <td style={{ fontSize: '12px', whiteSpace: 'nowrap' }}>{formatDate(tx.timestamp)}</td>
                                    <td>
                                        <span style={{
                                            display: 'inline-flex', padding: '2px 8px', borderRadius: '12px',
                                            fontSize: '10px', fontWeight: '600',
                                            background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)'
                                        }}>
                                            ✓ {tx.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Footer: count + pagination */}
            <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border)'
            }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Showing {startIdx + 1}–{Math.min(startIdx + PAGE_SIZE, filtered.length)} of {filtered.length} transactions
                    {filtered.length !== transactions.length && ` (${transactions.length} total)`}
                </span>

                {totalPages > 1 && (
                    <div className="pagination">
                        <button
                            className="page-btn"
                            disabled={safeCurrentPage <= 1}
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        >
                            ←
                        </button>
                        {getPageRange().map((p, i) =>
                            p === '...' ? (
                                <span key={`e${i}`} className="page-ellipsis">…</span>
                            ) : (
                                <button
                                    key={p}
                                    className={`page-btn ${p === safeCurrentPage ? 'active' : ''}`}
                                    onClick={() => setCurrentPage(p)}
                                >
                                    {p}
                                </button>
                            )
                        )}
                        <button
                            className="page-btn"
                            disabled={safeCurrentPage >= totalPages}
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        >
                            →
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default TransactionList;
