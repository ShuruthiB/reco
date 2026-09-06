import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Wallet, CheckCircle2, XCircle, Calculator, ChevronRight } from 'lucide-react';

interface OptimizerOpportunity {
  transaction_id: string;
  action: string;
  amount: number;
  expected_incremental_value: number;
  intervention_cost: number;
  net_incremental_value: number;
  roi: number;
  rejected: boolean;
  rejection_reason?: string;
}

interface OptimizerResponse {
  total_budget: number;
  budget_allocated: number;
  budget_remaining: number;
  top_opportunities: OptimizerOpportunity[];
  rejected_opportunities: OptimizerOpportunity[];
}

export function RecoveryBudgetScreen() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizerResponse | null>(null);
  
  const [constraints, setConstraints] = useState({
    total_budget: 25000,
    max_customer_incentive: 50,
    max_discount: 15,
    max_retries: 3,
    min_confidence: 0.6,
    allowed_interventions: ['RETRY', 'REMINDER', 'INCENTIVE', 'ALTERNATIVE_METHOD']
  });

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/optimizer/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(constraints)
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        alert("Failed to run simulation. Please ensure there are enough recent transactions.");
      }
    } catch (err) {
      console.error(err);
      alert("Failed to connect to backend API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Recovery Budget Optimizer</h1>
          <p className="text-sm text-slate-500">Simulate Knapsack allocation of limited funds to maximum ROI interventions.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="col-span-1 border border-slate-200">
          <CardHeader className="bg-slate-50 border-b border-slate-100 pb-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Calculator className="w-4 h-4 text-indigo-500" />
              Optimizer Constraints
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Total Intervention Budget ($)</label>
              <input type="number" className="w-full p-2 border border-slate-300 rounded text-sm" value={constraints.total_budget} onChange={e => setConstraints({...constraints, total_budget: parseFloat(e.target.value)})} />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Max Customer Incentive ($)</label>
              <input type="number" className="w-full p-2 border border-slate-300 rounded text-sm" value={constraints.max_customer_incentive} onChange={e => setConstraints({...constraints, max_customer_incentive: parseFloat(e.target.value)})} />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Max Discount (%)</label>
              <input type="number" className="w-full p-2 border border-slate-300 rounded text-sm" value={constraints.max_discount} onChange={e => setConstraints({...constraints, max_discount: parseFloat(e.target.value)})} />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Min AI Confidence (0.0 - 1.0)</label>
              <input type="number" step="0.1" className="w-full p-2 border border-slate-300 rounded text-sm" value={constraints.min_confidence} onChange={e => setConstraints({...constraints, min_confidence: parseFloat(e.target.value)})} />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Max Retries</label>
              <input type="number" className="w-full p-2 border border-slate-300 rounded text-sm" value={constraints.max_retries} onChange={e => setConstraints({...constraints, max_retries: parseInt(e.target.value)})} />
            </div>
            
            <div className="pt-4 mt-4 border-t border-slate-100">
              <Button onClick={handleSimulate} className="w-full justify-center" disabled={loading}>
                {loading ? 'Simulating...' : 'Run Simulation'}
              </Button>
              <p className="text-xs text-center text-slate-400 mt-2">Does not execute live actions.</p>
            </div>
          </CardContent>
        </Card>

        <div className="col-span-2 space-y-6">
          {!result ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 bg-slate-50 border border-dashed border-slate-200 rounded-lg py-12">
              <Wallet className="w-12 h-12 mb-4 text-slate-300" />
              <p>Run the simulation to see budget allocation.</p>
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
                  <p className="text-xs font-medium text-slate-500 mb-1">Total Budget</p>
                  <p className="text-2xl font-bold text-slate-900">${result.total_budget.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-lg shadow-sm">
                  <p className="text-xs font-medium text-emerald-700 mb-1">Allocated</p>
                  <p className="text-2xl font-bold text-emerald-700">${result.budget_allocated.toLocaleString()}</p>
                </div>
                <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-lg shadow-sm">
                  <p className="text-xs font-medium text-indigo-700 mb-1">Remaining</p>
                  <p className="text-2xl font-bold text-indigo-700">${result.budget_remaining.toLocaleString()}</p>
                </div>
              </div>

              {/* Funded Opportunities */}
              <Card>
                <CardHeader className="bg-emerald-50/50 border-b border-emerald-100 pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2 text-emerald-800">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Top Funded Opportunities
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-2 font-medium">Tx ID</th>
                        <th className="px-4 py-2 font-medium">Action</th>
                        <th className="px-4 py-2 font-medium text-right">Cost</th>
                        <th className="px-4 py-2 font-medium text-right">Net Value</th>
                        <th className="px-4 py-2 font-medium text-right">ROI</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {result.top_opportunities.length === 0 ? (
                        <tr><td colSpan={5} className="p-4 text-center text-slate-500">No opportunities funded.</td></tr>
                      ) : result.top_opportunities.map(opp => (
                        <tr key={opp.transaction_id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-mono text-xs text-slate-500">{opp.transaction_id.slice(0, 8)}...</td>
                          <td className="px-4 py-3 font-medium text-slate-700">{opp.action}</td>
                          <td className="px-4 py-3 text-right text-red-600">${Number(opp.intervention_cost).toFixed(2)}</td>
                          <td className="px-4 py-3 text-right text-emerald-600 font-medium">${Number(opp.net_incremental_value).toFixed(2)}</td>
                          <td className="px-4 py-3 text-right text-slate-600">{Number(opp.roi) > 1000 ? '∞' : Number(opp.roi).toFixed(1)}x</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>

              {/* Rejected Opportunities */}
              <Card>
                <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-700">
                    <XCircle className="w-4 h-4 text-slate-400" />
                    Rejected Opportunities
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 font-medium">Tx ID</th>
                          <th className="px-4 py-2 font-medium">Action</th>
                          <th className="px-4 py-2 font-medium">Rejection Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {result.rejected_opportunities.length === 0 ? (
                          <tr><td colSpan={3} className="p-4 text-center text-slate-500">No opportunities rejected.</td></tr>
                        ) : result.rejected_opportunities.map((opp, idx) => (
                          <tr key={`${opp.transaction_id}-${idx}`} className="hover:bg-slate-50">
                            <td className="px-4 py-2 font-mono text-xs text-slate-500">{opp.transaction_id.slice(0, 8)}...</td>
                            <td className="px-4 py-2 text-slate-600">{opp.action}</td>
                            <td className="px-4 py-2 text-red-600 text-xs flex items-center gap-1">
                              <ChevronRight className="w-3 h-3" />
                              {opp.rejection_reason}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
