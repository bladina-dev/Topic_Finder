import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import DiscoveryPage from './pages/DiscoveryPage';
import AnglesPage from './pages/AnglesPage';
import SourcesPage from './pages/SourcesPage';
import BrandPage from './pages/BrandPage';
import SettingsPage from './pages/SettingsPage';
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<DiscoveryPage />} />
              <Route path="/angles" element={<AnglesPage />} />
              <Route path="/sources" element={<SourcesPage />} />
              <Route path="/brand" element={<BrandPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
