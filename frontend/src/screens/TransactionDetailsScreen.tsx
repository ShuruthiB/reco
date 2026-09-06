import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { ArrowLeft, ShieldAlert, CreditCard, Activity, Loader2 } from 'lucide-react';

export function TransactionDetailsScreen() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [transaction, setTransaction] = useState<any>(null);
  const [decision, setDecision] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    
    Promise.all([
      fetch(`/api/transactions/${id}`).then(r => r.json()),
      fetch(`/api/transactions/${id}/decisions`).then(r => r.json())
    ])
    .then(([txData, decData]) => {
      setTransaction(txData);
      if (decData && decData.length > 0) {
        // Just take the first/latest decision for display
        setDecision(decData[0]);
      }
      setLoading(false);
    })
    .catch(err => {
      console.error("Error fetching transaction details:", err);
      setLoading(false);
    });
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="p-6 text-center text-slate-500">
        Transaction not found.
        <br />
        <Button variant="ghost" className="mt-4" onClick={() => navigate('/transactions')}>
          Return to list
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/transactions')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Transaction Details</h1>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle>Information</CardTitle>
              <Badge variant={transaction.status === 'recovered' ? 'success' : transaction.status === 'failed' ? 'danger' : 'warning'}>
                {transaction.status.toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-slate-500">Transaction ID</p>
                <p className="mt-1 font-mono text-sm">{transaction.id}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Customer</p>
                <p className="mt-1 text-sm font-medium">{transaction.customer_name || 'Anonymous'}</p>
                <p className="text-xs text-slate-500">{transaction.customer_email || 'No email'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Amount</p>
                <p className="mt-1 text-lg font-bold">${Number(transaction.amount).toFixed(2)} {transaction.currency}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Provider</p>
                <p className="mt-1 text-sm flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-slate-400" />
                  {transaction.provider}
                </p>
              </div>
              {transaction.failure_reason && (
                <div className="col-span-2 bg-red-50 p-3 rounded-md border border-red-100 mt-2">
                  <p className="text-xs font-semibold text-red-800 uppercase tracking-wider mb-1">Failure Reason</p>
                  <p className="text-sm text-red-900">{transaction.failure_reason.replace(/_/g, ' ')}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk & AI Decision</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-2">Risk Level</p>
              <div className="flex items-center gap-2">
                <ShieldAlert className={`w-5 h-5 ${(transaction.risk_level || 'low') === 'high' ? 'text-red-500' : 'text-yellow-500'}`} />
                <span className="font-medium capitalize">{transaction.risk_level || 'low'} Risk</span>
              </div>
            </div>
            <hr className="border-slate-100" />
            <div>
              <p className="text-sm font-medium text-slate-500 mb-2">AI Recommendation</p>
              {decision ? (
                <div className="space-y-3">
                  <Badge variant="neutral" className="bg-indigo-50 text-indigo-700 border border-indigo-100">
                    <Activity className="w-3 h-3 mr-1" />
                    {decision.recommended_action?.replace(/_/g, ' ')}
                  </Badge>
                  <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100">
                    {decision.rationale}
                  </p>
                  <Link to={`/decisions`} className="text-xs text-indigo-600 hover:underline font-medium">
                    View in AI Decision Center &rarr;
                  </Link>
                </div>
              ) : (
                <p className="text-sm text-slate-500 italic">
                  {transaction.status?.toLowerCase() === 'success' ? 'Not applicable (Payment successful on first attempt).' : 'No AI decision recorded.'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
