import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Login } from './components/Login';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Overview } from './components/Overview';
import { ApplicationKeys } from './components/ApplicationKeys';
import { UserDirectory } from './components/UserDirectory';
import { RevenuePlans } from './components/RevenuePlans';
import { CentralLogs } from './components/CentralLogs';
import { ApiSandbox } from './components/ApiSandbox';

export function App() {
  const { token } = useAuth();
  const [currentTab, setTab] = useState('overview');

  if (!token) {
    return <Login />;
  }

  const tabTitles = {
    overview: { title: 'Dashboard Overview', subtitle: 'Centralized platform analytics and activity monitoring' },
    applications: { title: 'Application API Keys', subtitle: 'Manage API credentials for connected standalone applications' },
    users: { title: 'Central User Directory', subtitle: 'View registered user identities across applications' },
    revenue: { title: 'Revenue & Subscriptions', subtitle: 'Payment transactions (₹ INR) and application subscriptions' },
    logs: { title: 'Central Application Logs', subtitle: 'Real-time security and audit logs from connected apps' },
    sandbox: { title: 'API Sandbox Tester', subtitle: 'Test Unified Backend REST endpoints interactively' },
  };

  const activeTabInfo = tabTitles[currentTab] || tabTitles.overview;

  return (
    <div className="app-layout">
      <Sidebar currentTab={currentTab} setTab={setTab} />

      <div className="main-wrapper">
        <Header
          title={activeTabInfo.title}
          subtitle={activeTabInfo.subtitle}
        />

        <main className="main-content">
          {currentTab === 'overview' && <Overview />}
          {currentTab === 'applications' && <ApplicationKeys />}
          {currentTab === 'users' && <UserDirectory />}
          {currentTab === 'revenue' && <RevenuePlans />}
          {currentTab === 'logs' && <CentralLogs />}
          {currentTab === 'sandbox' && <ApiSandbox />}
        </main>
      </div>
    </div>
  );
}

export default App;
