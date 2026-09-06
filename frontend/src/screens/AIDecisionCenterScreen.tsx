import { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { DataTable } from '../components/ui/DataTable';
import { BrainCircuit, CheckCircle2, XCircle, AlertCircle, TrendingUp, ShieldAlert, FileText, Ban, Loader2 } from 'lucide-react';

const formatCurrency = (val: number) => `$${Number(val).toFixed(2)}`;
const formatPercent = (val: number) => `${(Number(val) * 100).toFixed(1)}%`;

const getActionStyle = (action: string) => {
  if (action === 'DO_NOTHING') return "bg-slate-100 text-slate-700 border-slate-200";
  if (action === 'FINANCIAL' || action === 'RETRY' || action === 'INCENTIVE') return "bg-emerald-100 text-emerald-700 border-emerald-200";
  if (action === 'COMMUNICATION' || action === 'REMINDER' || action === 'REMINDER_EMAIL') return "bg-blue-100 text-blue-700 border-blue-200";
  if (action === 'ESCALATION' || action === 'ESCALATE' || action === 'MANUAL_REVIEW') return "bg-rose-100 text-rose-700 border-rose-200";
  return "bg-purple-100 text-purple-700 border-purple-200"; // Fallback for ALTERNATIVE_METHOD etc
};

export function AIDecisionCenterScreen() {
  const [decisions, setDecisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/decisions')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
        return res.json();
      })
      .then(data => {
        setDecisions(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setDecisions([]);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">AI Decision Center</h1>
        <p className="text-base text-slate-500 max-w-3xl">
          Transparent view into the ML engine's economic calculations. 
          See how RECO evaluates multiple interventions, accounts for costs, bounds decisions by policy, and selects the most profitable path.
        </p>
      </div>

      <div className="space-y-8">
        {decisions.length === 0 ? (
          <div className="text-center py-12 text-slate-500">No decisions found.</div>
        ) : decisions.map(decision => (
          <Card key={decision.id} className="overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            {/* 1. Money is at risk */}
            <div className="bg-slate-900 text-white p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-indigo-500/20 rounded-xl border border-indigo-500/30">
                  <ShieldAlert className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg tracking-tight">Transaction {decision.transaction_id}</h3>
                  <div className="flex items-center gap-3 mt-1 text-sm">
                    <span className="text-slate-400 flex items-center gap-1">
                      Value at Risk: <span className="text-blue-400 font-bold numeric-data tracking-tight">{formatCurrency(decision.amount)}</span>
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="flex items-center gap-1 text-slate-400">
                      Risk Profile: 
                      <Badge variant={decision.risk === 'high' ? 'danger' : decision.risk === 'medium' ? 'warning' : 'neutral'} className="ml-1 uppercase text-[10px]">
                        {decision.risk}
                      </Badge>
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right flex flex-col md:items-end">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Action Selected by Engine</p>
                <div className={`px-3 py-1.5 rounded-full border text-sm font-semibold flex items-center gap-2 ${getActionStyle(decision.recommended_action)} w-fit`}>
                  {decision.recommended_action === 'DO_NOTHING' ? <Ban className="w-4 h-4" /> : <BrainCircuit className="w-4 h-4" />}
                  {decision.recommended_action.replace(/_/g, ' ')}
                </div>
              </div>
            </div>
            
            <CardContent className="p-0">
              <div className="grid lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
                {/* 2, 3, 4, 7. Interventions, Incremental Impact, Cost, Auditable Bounds */}
                <div className="p-0 col-span-2 flex flex-col">
                  <div className="p-5 pb-3 border-b border-slate-100 bg-slate-50/50">
                    <h4 className="font-semibold text-sm text-slate-900 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-slate-400" />
                      Candidate Interventions Matrix
                    </h4>
                    <p className="text-xs text-slate-500 mt-1">Comparing natural recovery versus active interventions.</p>
                  </div>
                  
                  <DataTable 
                    className="border-none shadow-none rounded-none"
                    data={decision.candidates}
                    columns={[
                      { 
                        header: 'Candidate Action', 
                        cell: (c: any) => (
                          <span className={`font-medium ${c.action === decision.recommended_action ? 'text-slate-900' : 'text-slate-600'}`}>
                            {c.action.replace(/_/g, ' ')}
                            {c.action === decision.recommended_action && <Badge variant="success" className="ml-2 text-[10px]">Selected</Badge>}
                          </span>
                        ) 
                      },
                      { 
                        header: 'Estimated Uplift', 
                        className: 'text-right',
                        cell: (c: any) => <span className="numeric-data text-emerald-600">{formatPercent(c.predicted_uplift)}</span> 
                      },
                      { 
                        header: 'Gross Expected', 
                        className: 'text-right',
                        cell: (c: any) => <span className="numeric-data text-blue-600">{formatCurrency(c.expected_revenue)}</span> 
                      },
                      { 
                        header: 'Intervention Cost', 
                        className: 'text-right',
                        cell: (c: any) => <span className="numeric-data text-rose-600">{c.cost > 0 ? `-${formatCurrency(c.cost)}` : formatCurrency(0)}</span> 
                      },
                      { 
                        header: 'Net Return', 
                        className: 'text-right',
                        cell: (c: any) => <span className="numeric-data font-bold text-indigo-600">{formatCurrency(c.net_contribution)}</span> 
                      },
                      { 
                        header: 'Policy Bounds', 
                        className: 'text-center',
                        cell: (c: any) => c.policy_approved ? (
                          <div className="flex justify-center" title="Within merchant policy bounds">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          </div>
                        ) : (
                          <div className="flex justify-center" title={c.reject_reason}>
                            <XCircle className="w-4 h-4 text-rose-500" />
                          </div>
                        )
                      }
                    ]}
                  />
                </div>

                {/* 5, 6. Why it happened, DO NOTHING rationality */}
                <div className="bg-slate-50 flex flex-col h-full">
                  <div className="p-5 pb-3 border-b border-slate-100 bg-white">
                    <h4 className="font-semibold text-sm text-slate-900 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-slate-400" />
                      Engine Reasoning Log
                    </h4>
                  </div>
                  <div className="p-5 space-y-6 flex-1">
                    <div>
                      <h5 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Primary Rationale</h5>
                      <p className="text-sm text-slate-700 leading-relaxed bg-white p-3 rounded-lg border border-slate-200">
                        {decision.rationale}
                      </p>
                    </div>

                    <div>
                      <h5 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Prediction Confidence</h5>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${Number(decision.confidence) > 0.8 ? 'bg-emerald-500' : Number(decision.confidence) > 0.5 ? 'bg-amber-500' : 'bg-rose-500'}`} 
                            style={{ width: `${Number(decision.confidence) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-bold numeric-data tracking-tight text-slate-700">{decision.confidence != null ? (Number(decision.confidence) * 100).toFixed(0) : 0}%</span>
                      </div>
                    </div>

                    <div className="pt-4 mt-auto border-t border-slate-200/60">
                      <h5 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Audit Status</h5>
                      {decision.executed ? (
                        <div className="flex items-start gap-2 text-sm text-emerald-700 bg-emerald-100/50 p-2.5 rounded-lg border border-emerald-200">
                          <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <span>Executed automatically on <span className="font-medium numeric-data">{decision.executed_at ? new Date(decision.executed_at).toLocaleTimeString() : 'N/A'}</span></span>
                        </div>
                      ) : (
                        <div className="flex items-start gap-2 text-sm text-amber-700 bg-amber-100/50 p-2.5 rounded-lg border border-amber-200">
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <span>Awaiting execution or blocked by external limits</span>
                        </div>
                      )}
                    </div>
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
