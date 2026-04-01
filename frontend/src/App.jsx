import React, { useState } from 'react';
import Header from './components/Header';
import WalletInput from './components/WalletInput';
import StatsOverview from './components/StatsOverview';
import RiskAnalysis from './components/RiskAnalysis';
import TransactionGraph from './components/TransactionGraph';
import GraphExplanation from './components/GraphExplanation';
import TransactionList from './components/TransactionList';
import AIInsights from './components/AIInsights';
import { analyzeWallet } from './services/api';

function App() {
    const [currentPage, setCurrentPage] = useState('dashboard');
    const [walletAddress, setWalletAddress] = useState('');
    const [analysisData, setAnalysisData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleAnalyze = async (address) => {
        setIsLoading(true);
        setWalletAddress(address);
        setError(null);

        try {
            const data = await analyzeWallet(address);
            setAnalysisData(data);
        } catch (err) {
            console.error('Analysis failed:', err);
            setError(err.message);
            // Fallback to mock data for demo
            setAnalysisData(generateMockData(address));
        } finally {
            setIsLoading(false);
        }
    };

    const renderDashboard = () => (
        <div className="container">
            <WalletInput onAnalyze={handleAnalyze} isLoading={isLoading} />

            {isLoading && (
                <div className="loading-state">
                    <div className="loader"></div>
                    <p>Fetching blockchain data & running forensic analysis...</p>
                </div>
            )}

            {error && !isLoading && (
                <div className="error-banner">
                    <span className="icon">⚠️</span>
                    <div>
                        <p>{error}</p>
                        <small>Using demo data for visualization. Start the backend server for live analysis.</small>
                    </div>
                </div>
            )}

            {analysisData && !isLoading && (
                <div className="dashboard-grid fade-in">
                    <StatsOverview data={analysisData} />
                    <RiskAnalysis
                        riskScore={analysisData.riskScore}
                        riskLevel={analysisData.riskLevel}
                        riskBreakdown={analysisData.riskBreakdown}
                        aiInsights={analysisData.aiInsights}
                    />
                    <AIInsights insights={analysisData.aiInsights} address={analysisData.address} />
                    <TransactionGraph graphData={analysisData.graphData} />
                    <GraphExplanation graphExplanation={analysisData.graphExplanation} />
                    <TransactionList transactions={analysisData.transactions} />
                </div>
            )}
        </div>
    );

    return (
        <div className="app">
            <Header currentPage={currentPage} onNavigate={setCurrentPage} />
            <main className="main-content">
                {renderDashboard()}
            </main>
        </div>
    );
}

function generateMockData(address) {
    const riskScore = Math.floor(Math.random() * 60) + 20;
    return {
        address,
        blockchain: address.startsWith('0x') ? 'ethereum' : 'bitcoin',
        riskScore,
        riskLevel: riskScore >= 70 ? 'HIGH' : riskScore >= 40 ? 'MEDIUM' : 'LOW',
        totalTransactions: Math.floor(Math.random() * 500) + 50,
        totalVolume: `${(Math.random() * 100).toFixed(2)} ETH`,
        balance: `${(Math.random() * 10).toFixed(4)} ETH`,
        connectedWallets: Math.floor(Math.random() * 50) + 5,
        suspiciousActivities: Math.floor(Math.random() * 10),
        transactions: Array.from({ length: 15 }, (_, i) => ({
            id: `tx-${i + 1}`,
            hash: `0x${Math.random().toString(16).substr(2, 40)}`,
            type: Math.random() > 0.5 ? 'Sent' : 'Received',
            amount: `${(Math.random() * 5).toFixed(4)} ETH`,
            from: `0x${Math.random().toString(16).substr(2, 8)}...`,
            to: `0x${Math.random().toString(16).substr(2, 8)}...`,
            timestamp: new Date(Date.now() - Math.random() * 30 * 86400000).toISOString(),
            status: 'Confirmed',
            risk: Math.floor(Math.random() * 100)
        })),
        graphData: {
            nodes: [
                { id: 'target', label: 'Target Wallet', type: 'target', risk: riskScore },
                ...Array.from({ length: 8 }, (_, i) => ({
                    id: `w${i + 1}`, label: `Wallet ${i + 1}`,
                    type: i < 2 ? 'high-risk' : i < 5 ? 'medium-risk' : 'low-risk',
                    risk: Math.floor(Math.random() * 100)
                }))
            ],
            edges: Array.from({ length: 8 }, (_, i) => ({
                from: 'target', to: `w${i + 1}`,
                value: Math.random() * 10, label: `${(Math.random() * 5).toFixed(2)} ETH`
            }))
        },
        aiInsights: {
            summary: `This wallet exhibits ${riskScore >= 70 ? 'high' : riskScore >= 40 ? 'moderate' : 'low'}-risk behavioral patterns. ${riskScore >= 50 ? 'Multiple indicators suggest potential involvement in mixing services or exchange operations.' : 'Transaction patterns are consistent with normal wallet usage.'}`,
            riskFactors: [
                { title: 'Transaction Velocity', description: 'Elevated transaction frequency detected, processing above-average daily transactions.', severity: 'high', score: 12, maxScore: 15 },
                { title: 'Mixing Entropy', description: 'Moderate branching patterns detected in transaction graph.', severity: 'medium', score: 8, maxScore: 15 },
                { title: 'Amount Anomaly', description: 'Some irregularities in transaction value distribution noted.', severity: 'medium', score: 7, maxScore: 15 },
                { title: 'Connection Density', description: 'Connected to a moderate number of unique addresses.', severity: 'low', score: 4, maxScore: 10 }
            ],
            recommendations: [
                '🟡 Periodic monitoring recommended — reassess in 14 days',
                '🟡 Review connected wallet addresses for known entity matches',
                '🟡 Check for unusual pattern changes in upcoming transactions'
            ],
            confidence: 78,
            ai_model: 'demo-mode'
        },
        graphExplanation: {
            overview: `This wallet is connected to 8 other wallet addresses through 8 transaction links. The connected wallets show a mix of risk levels, with some exhibiting moderate activity patterns.`,
            key_findings: [
                'Moderate connectivity — the wallet is linked to 8 addresses, showing diversified transaction activity.',
                'The transaction network appears typical and does not raise immediate red flags.',
            ],
            ai_model: 'demo-mode'
        }
    };
}

export default App;
