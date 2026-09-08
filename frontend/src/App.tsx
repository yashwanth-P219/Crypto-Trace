import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { VictimDashboardPage } from './pages/VictimDashboardPage';
import { InvestigatorDashboardPage } from './pages/InvestigatorDashboardPage';
import { DashboardPage } from './pages/DashboardPage';
import { CasesPage } from './pages/CasesPage';
import { CreateCasePage } from './pages/CreateCasePage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { WalletAnalysisPage } from './pages/WalletAnalysisPage';
import { TransactionExplorer } from './components/TransactionExplorer';
import { GraphExplorer } from './components/GraphExplorer';
import { InvestigationAnalysis } from './components/InvestigationAnalysis';
import { PriorityQueueView } from './components/PriorityQueueView';
import { MultiChainExplorer } from './components/MultiChainExplorer';
import { MonitoringPage } from './pages/MonitoringPage';
import { AdminPage } from './pages/AdminPage';
import { ErrorBoundary } from './components/ErrorBoundary';
import { User } from './types';
import { api } from './services/api';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('sih_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [isSigningUp, setIsSigningUp] = useState(false);
  const [activeTab, setActiveTab] = useState<string>(() => {
    const saved = localStorage.getItem('sih_user');
    if (saved) {
      try {
        const u = JSON.parse(saved);
        if (u.role === 'VICTIM') return 'victim_dashboard';
        if (u.role === 'INVESTIGATOR') return 'investigator_dashboard';
      } catch (e) {}
    }
    return 'dashboard';
  });
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-SIH2026-001');
  const [inspectAddress, setInspectAddress] = useState<string>('');
  const [alertCount, setAlertCount] = useState<number>(0);

  useEffect(() => {
    if (currentUser) {
      api.getAlerts(true).then((alerts) => setAlertCount(alerts.length)).catch(() => {});
    }
  }, [currentUser, activeTab]);

  const handleLoginSuccess = (u: User) => {
    localStorage.setItem('sih_user', JSON.stringify(u));
    setCurrentUser(u);
    if (u.role === 'VICTIM') {
      setActiveTab('victim_dashboard');
    } else if (u.role === 'INVESTIGATOR') {
      setActiveTab('investigator_dashboard');
    } else {
      setActiveTab('dashboard');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('sih_auth_token');
    localStorage.removeItem('sih_user');
    setCurrentUser(null);
    setIsSigningUp(false);
  };

  const handleOpenCase = (caseId: string) => {
    setSelectedCaseId(caseId);
    setActiveTab('case_detail');
  };

  const handleInspectWallet = (address: string) => {
    setInspectAddress(address);
    setActiveTab('wallets');
  };

  if (!currentUser) {
    if (isSigningUp) {
      return (
        <SignupPage
          onSwitchToLogin={() => setIsSigningUp(false)}
          onSignupSuccess={() => setIsSigningUp(false)}
        />
      );
    }
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        onSwitchToSignup={() => setIsSigningUp(true)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col font-sans">
      <Navbar
        currentUser={currentUser}
        onLogout={handleLogout}
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        alertCount={alertCount}
        onOpenCase={handleOpenCase}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <ErrorBoundary fallbackTitle="Application View Error">
          {activeTab === 'victim_dashboard' && (
          <VictimDashboardPage
            currentUser={currentUser}
            onOpenCase={handleOpenCase}
            onCreateNewCase={() => setActiveTab('create_case')}
          />
        )}

        {activeTab === 'investigator_dashboard' && (
          <InvestigatorDashboardPage
            currentUser={currentUser}
            onOpenCase={handleOpenCase}
          />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage
            onOpenCase={handleOpenCase}
            onNavigateToWallets={() => setActiveTab('wallets')}
          />
        )}

        {activeTab === 'cases' && (
          <CasesPage
            currentUser={currentUser}
            onOpenCase={handleOpenCase}
            onCreateNewCase={() => setActiveTab('create_case')}
          />
        )}

        {activeTab === 'create_case' && (
          <CreateCasePage
            currentUser={currentUser}
            onCaseCreated={(newId) => handleOpenCase(newId)}
            onCancel={() => {
              if (currentUser?.role === 'VICTIM') setActiveTab('victim_dashboard');
              else if (currentUser?.role === 'INVESTIGATOR') setActiveTab('investigator_dashboard');
              else setActiveTab('cases');
            }}
          />
        )}

        {activeTab === 'case_detail' && (
          <CaseDetailPage
            caseId={selectedCaseId}
            currentUser={currentUser}
            onBack={() => setActiveTab('cases')}
            onInspectWallet={handleInspectWallet}
          />
        )}

        {activeTab === 'wallets' && (
          <WalletAnalysisPage initialAddress={inspectAddress} />
        )}

        {activeTab === 'transactions' && (
          <TransactionExplorer initialAddress={inspectAddress || '0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97'} />
        )}

        {activeTab === 'graph' && (
          <GraphExplorer
            initialAddress={inspectAddress || '0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97'}
            onInspectWallet={handleInspectWallet}
          />
        )}

        {activeTab === 'priority' && (
          <PriorityQueueView
            currentUser={currentUser}
            onInspectWallet={handleInspectWallet}
            onOpenCase={handleOpenCase}
          />
        )}

        {activeTab === 'intelligence' && (
          <InvestigationAnalysis
            initialWallet={inspectAddress || '0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97'}
            onSelectTx={(tx) => {
              setInspectAddress(tx);
              setActiveTab('transactions');
            }}
          />
        )}

        {activeTab === 'multichain' && (
          <MultiChainExplorer
            currentUser={currentUser}
            onInspectWallet={handleInspectWallet}
          />
        )}

        {activeTab === 'monitoring' && (
          <MonitoringPage />
        )}

        {activeTab === 'admin' && (
          <AdminPage />
        )}
        </ErrorBoundary>
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-600 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-2">
          <span className="font-semibold text-slate-800">CryptoTrace Defense Forensics</span>
          <span className="font-mono text-[11px] text-slate-500">
            Automated Blockchain Forensics & VASP Identification Platform
          </span>
          <span className="text-[10px] px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 font-medium">
            Forensic Engine: Live On-Chain & Case Dossier Sync
          </span>
        </div>
      </footer>
    </div>
  );
}

export default App;
