export type TransactionStatus = 'pending' | 'recovered' | 'failed' | 'quarantined';
export type RiskLevel = 'low' | 'medium' | 'high';
export type ActionType = 'DO_NOTHING' | 'RETRY' | 'REMINDER_EMAIL' | 'REMINDER_SMS' | 'INCENTIVE_10' | 'INCENTIVE_20';

export interface Transaction {
  id: string;
  customerName: string;
  customerEmail: string;
  amount: number;
  currency: string;
  status: TransactionStatus;
  riskLevel: RiskLevel;
  createdAt: string;
  lastAttemptAt: string;
  provider: string;
  failureReason?: string;
}

export interface DecisionCandidate {
  action: ActionType;
  predictedUplift: number;
  expectedRevenue: number;
  cost: number;
  netContribution: number;
  policyApproved: boolean;
  rejectReason?: string;
}

export interface Decision {
  id: string;
  transactionId: string;
  amount: number;
  risk: RiskLevel;
  candidates: DecisionCandidate[];
  recommendedAction: ActionType;
  confidence: number;
  rationale: string;
  executed: boolean;
  executedAt?: string;
}

export interface Experiment {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'draft';
  startDate: string;
  endDate?: string;
  arms: { name: string; trafficShare: number; incrementalUplift: number }[];
  totalTransactions: number;
  incrementalRevenue: number;
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive';
  lastUpdated: string;
  rules: string[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  type: 'DECISION_EVALUATED' | 'ACTION_EXECUTED' | 'POLICY_UPDATED' | 'BUDGET_ADJUSTED';
  actor: string;
  details: string;
}

export const MOCK_TRANSACTIONS: Transaction[] = [
  { id: 'txn_1001', customerName: 'Alice Johnson', customerEmail: 'alice@example.com', amount: 1250.00, currency: 'USD', status: 'pending', riskLevel: 'high', createdAt: '2026-09-05T08:12:00Z', lastAttemptAt: '2026-09-05T08:12:00Z', provider: 'Razorpay', failureReason: 'insufficient_funds' },
  { id: 'txn_1002', customerName: 'Bob Smith', customerEmail: 'bob@example.com', amount: 45.00, currency: 'USD', status: 'recovered', riskLevel: 'low', createdAt: '2026-09-04T14:22:00Z', lastAttemptAt: '2026-09-04T16:30:00Z', provider: 'Razorpay', failureReason: 'temporary_hold' },
  { id: 'txn_1003', customerName: 'Charlie Davis', customerEmail: 'charlie@example.com', amount: 300.00, currency: 'USD', status: 'failed', riskLevel: 'medium', createdAt: '2026-09-03T09:15:00Z', lastAttemptAt: '2026-09-05T09:15:00Z', provider: 'Razorpay', failureReason: 'card_expired' },
  { id: 'txn_1004', customerName: 'Diana Prince', customerEmail: 'diana@example.com', amount: 890.50, currency: 'USD', status: 'pending', riskLevel: 'high', createdAt: '2026-09-05T10:05:00Z', lastAttemptAt: '2026-09-05T10:05:00Z', provider: 'Razorpay', failureReason: 'do_not_honor' },
  { id: 'txn_1005', customerName: 'Evan Wright', customerEmail: 'evan@example.com', amount: 15.99, currency: 'USD', status: 'quarantined', riskLevel: 'low', createdAt: '2026-09-05T11:00:00Z', lastAttemptAt: '2026-09-05T11:00:00Z', provider: 'Razorpay', failureReason: 'suspected_fraud' },
];

export const MOCK_DECISIONS: Decision[] = [
  {
    id: 'dec_901',
    transactionId: 'txn_1001',
    amount: 1250.00,
    risk: 'high',
    recommendedAction: 'INCENTIVE_10',
    confidence: 0.82,
    rationale: 'High value transaction with insufficient funds. 10% incentive shows highest net contribution without violating max discount policy.',
    executed: true,
    executedAt: '2026-09-05T08:15:00Z',
    candidates: [
      { action: 'DO_NOTHING', predictedUplift: 0, expectedRevenue: 0, cost: 0, netContribution: 0, policyApproved: true },
      { action: 'RETRY', predictedUplift: 0.05, expectedRevenue: 62.50, cost: 0.50, netContribution: 62.00, policyApproved: true },
      { action: 'REMINDER_EMAIL', predictedUplift: 0.08, expectedRevenue: 100.00, cost: 0.01, netContribution: 99.99, policyApproved: true },
      { action: 'INCENTIVE_10', predictedUplift: 0.45, expectedRevenue: 562.50, cost: 125.00, netContribution: 437.50, policyApproved: true },
      { action: 'INCENTIVE_20', predictedUplift: 0.48, expectedRevenue: 600.00, cost: 250.00, netContribution: 350.00, policyApproved: false, rejectReason: 'Exceeds maximum incentive policy for this segment' }
    ]
  },
  {
    id: 'dec_902',
    transactionId: 'txn_1004',
    amount: 890.50,
    risk: 'high',
    recommendedAction: 'REMINDER_SMS',
    confidence: 0.65,
    rationale: 'Do not honor error typically resolves with customer contact. SMS has higher conversion rate than email for this cohort.',
    executed: false,
    candidates: [
      { action: 'DO_NOTHING', predictedUplift: 0, expectedRevenue: 0, cost: 0, netContribution: 0, policyApproved: true },
      { action: 'RETRY', predictedUplift: 0.02, expectedRevenue: 17.81, cost: 0.50, netContribution: 17.31, policyApproved: true },
      { action: 'REMINDER_SMS', predictedUplift: 0.15, expectedRevenue: 133.57, cost: 0.05, netContribution: 133.52, policyApproved: true },
      { action: 'INCENTIVE_10', predictedUplift: 0.18, expectedRevenue: 160.29, cost: 89.05, netContribution: 71.24, policyApproved: true }
    ]
  }
];

export const MOCK_EXPERIMENTS: Experiment[] = [
  {
    id: 'exp_01',
    name: 'Smart Retries vs Fixed Schedule',
    status: 'active',
    startDate: '2026-08-15T00:00:00Z',
    totalTransactions: 15420,
    incrementalRevenue: 42500,
    arms: [
      { name: 'Control (Fixed 24h)', trafficShare: 0.1, incrementalUplift: 0 },
      { name: 'Treatment (ML Timing)', trafficShare: 0.9, incrementalUplift: 0.12 }
    ]
  },
  {
    id: 'exp_02',
    name: 'Dynamic Incentives for High Risk',
    status: 'active',
    startDate: '2026-09-01T00:00:00Z',
    totalTransactions: 3200,
    incrementalRevenue: 18400,
    arms: [
      { name: 'Control (No Incentive)', trafficShare: 0.5, incrementalUplift: 0 },
      { name: 'Treatment (5-15% Dynamic)', trafficShare: 0.5, incrementalUplift: 0.28 }
    ]
  }
];

export const MOCK_POLICIES: Policy[] = [
  {
    id: 'pol_1',
    name: 'Maximum Incentive Limit',
    description: 'Caps the maximum discount offered to any user based on their lifetime value tier.',
    status: 'active',
    lastUpdated: '2026-08-10T10:00:00Z',
    rules: ['If LTV < $1000, Max Incentive = 10%', 'If LTV >= $1000, Max Incentive = 20%']
  },
  {
    id: 'pol_2',
    name: 'Contact Frequency Cap',
    description: 'Prevents spamming customers with multiple recovery attempts across different transactions.',
    status: 'active',
    lastUpdated: '2026-07-22T14:30:00Z',
    rules: ['Max 2 SMS per week per customer', 'Max 3 Emails per week per customer']
  }
];

export const MOCK_AUDIT: AuditEvent[] = [
  { id: 'aud_1001', timestamp: '2026-09-05T10:05:12Z', type: 'DECISION_EVALUATED', actor: 'System (ML Engine)', details: 'Evaluated txn_1004. Recommended REMINDER_SMS.' },
  { id: 'aud_1002', timestamp: '2026-09-05T09:30:00Z', type: 'BUDGET_ADJUSTED', actor: 'Alice (Admin)', details: 'Increased monthly recovery incentive budget by $5,000.' },
  { id: 'aud_1003', timestamp: '2026-09-05T08:15:02Z', type: 'ACTION_EXECUTED', actor: 'System (Execution Engine)', details: 'Dispatched INCENTIVE_10 email for txn_1001.' },
];

export const MOCK_DASHBOARD_METRICS = {
  revenueAtRisk: 124500.00,
  naturalRecovery: 45200.00,
  aiIncrementalRevenue: 38400.00,
  interventionCost: 4200.00,
  netIncrementalRevenue: 34200.00,
  recoveryRate: 0.67,
  incrementalLift: 0.18,
  activeExperiments: 2,
  pendingEscalations: 5
};
