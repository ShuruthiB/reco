import { MOCK_DECISIONS } from '../data/mock';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { DataTable } from '../components/ui/DataTable';
import { BrainCircuit, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

export function AIDecisionCenterScreen() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">AI Decision Center</h1>
          <p className="text-sm text-slate-500">Transparent view into the ML engine's economic calculations and action selection.</p>
        </div>
      </div>

      <div className="space-y-6">
        {MOCK_DECISIONS.map(decision => (
          <Card key={decision.id} className="overflow-hidden">
            <div className="bg-slate-900 text-white p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <BrainCircuit className="w-8 h-8 text-indigo-400" />
                <div>
                  <h3 className="font-semibold text-lg">Transaction {decision.transactionId}</h3>
                  <p className="text-slate-400 text-sm">Amount: ${decision.amount.toFixed(2)} • Risk: <span className="uppercase">{decision.risk}</span></p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-400 mb-1">Recommended Action</p>
                <Badge variant="neutral" className="bg-white/10 text-white border-white/20">
                  {decision.recommendedAction.replace(/_/g, ' ')}
                </Badge>
              </div>
            </div>
            
            <CardContent className="p-0">
              <div className="grid md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-200">
                <div className="p-6 col-span-2 space-y-4">
                  <h4 className="font-semibold text-sm text-slate-900">Candidate Actions Evaluation</h4>
                  <DataTable 
                    data={decision.candidates}
                    columns={[
                      { header: 'Action', cell: (c) => <span className="font-medium">{c.action.replace(/_/g, ' ')}</span> },
                      { header: 'Uplift', cell: (c) => `${(c.predictedUplift * 100).toFixed(1)}%` },
                      { header: 'Exp Revenue', cell: (c) => `$${c.expectedRevenue.toFixed(2)}` },
                      { header: 'Cost', cell: (c) => <span className="text-slate-500">-${c.cost.toFixed(2)}</span> },
                      { header: 'Net Contribution', cell: (c) => <span className="font-bold text-emerald-600">${c.netContribution.toFixed(2)}</span> },
                      { 
                        header: 'Policy Check', 
                        cell: (c) => c.policyApproved ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        ) : (
                          <div title={c.rejectReason}><XCircle className="w-4 h-4 text-red-500" /></div>
                        )
                      }
                    ]}
                  />
                </div>
                <div className="p-6 space-y-6 bg-slate-50">
                  <div>
                    <h4 className="font-semibold text-sm text-slate-900 mb-2">Rationale</h4>
                    <p className="text-sm text-slate-600 bg-white p-3 rounded border border-slate-200">
                      {decision.rationale}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-slate-900 mb-2">Confidence Score</h4>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${decision.confidence > 0.8 ? 'bg-emerald-500' : decision.confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                          style={{ width: `${decision.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{(decision.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-slate-900 mb-2">Execution Status</h4>
                    {decision.executed ? (
                      <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 p-2 rounded border border-emerald-100">
                        <CheckCircle2 className="w-4 h-4" />
                        Executed at {new Date(decision.executedAt!).toLocaleTimeString()}
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 p-2 rounded border border-amber-100">
                        <AlertCircle className="w-4 h-4" />
                        Awaiting execution / Blocked
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
