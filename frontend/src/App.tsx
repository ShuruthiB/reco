import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { OverviewDashboard } from './screens/OverviewDashboard';
import { TransactionsScreen } from './screens/TransactionsScreen';
import { TransactionDetailsScreen } from './screens/TransactionDetailsScreen';
import { AIDecisionCenterScreen } from './screens/AIDecisionCenterScreen';
import { InterventionSimulatorScreen } from './screens/InterventionSimulatorScreen';
import { ExperimentsScreen } from './screens/ExperimentsScreen';
import { RecoveryBudgetScreen } from './screens/RecoveryBudgetScreen';
import { PoliciesScreen } from './screens/PoliciesScreen';
import { AuditTrailScreen } from './screens/AuditTrailScreen';
import { SystemHealthScreen } from './screens/SystemHealthScreen';
import { SettingsScreen } from './screens/SettingsScreen';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<OverviewDashboard />} />
          <Route path="transactions" element={<TransactionsScreen />} />
          <Route path="transactions/:id" element={<TransactionDetailsScreen />} />
          <Route path="decisions" element={<AIDecisionCenterScreen />} />
          <Route path="simulator" element={<InterventionSimulatorScreen />} />
          <Route path="experiments" element={<ExperimentsScreen />} />
          <Route path="budget" element={<RecoveryBudgetScreen />} />
          <Route path="policies" element={<PoliciesScreen />} />
          <Route path="audit" element={<AuditTrailScreen />} />
          <Route path="health" element={<SystemHealthScreen />} />
          <Route path="settings" element={<SettingsScreen />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
