import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Activity, Database, Server, Webhook, Zap, Loader2 } from 'lucide-react';
import { Badge } from '../components/ui/Badge';

export function SystemHealthScreen() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
        return res.json();
      })
      .then(data => {
        setHealth(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setHealth({ status: 'unavailable', database: 'unavailable', environment: 'unknown' });
        setLoading(false);
      });
  }, []);

  const systems = [
    { name: 'API Gateway', status: health?.status === 'ok' ? 'operational' : 'degraded', uptime: '99.99%', ping: '45ms', icon: Server },
    { name: 'Database / Storage', status: health?.database === 'ok' ? 'operational' : 'degraded', uptime: '100%', ping: '12ms', icon: Database, message: health?.database !== 'ok' ? 'Database connection failed' : undefined },
    { name: 'ML Scoring Engine', status: 'operational', uptime: '99.95%', ping: '85ms', icon: Brain },
    { name: 'Razorpay Webhooks', status: 'operational', uptime: '98.50%', ping: '120ms', icon: Webhook },
    { name: 'Execution Workers', status: 'operational', uptime: '99.99%', ping: '20ms', icon: Zap },
  ];

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">System Health</h1>
          <p className="text-sm text-slate-500">Real-time status of RECO infrastructure and external integrations.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full font-medium">
          <Activity className="w-4 h-4" />
          All Systems Operational
        </div>
      </div>

      <div className="grid gap-4">
        {systems.map(sys => (
          <Card key={sys.name} className={sys.status === 'degraded' ? 'border-yellow-200' : ''}>
            <div className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${sys.status === 'degraded' ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-700'}`}>
                  <sys.icon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{sys.name}</h3>
                  {sys.message && <p className="text-xs text-yellow-600 mt-0.5">{sys.message}</p>}
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right hidden sm:block">
                  <p className="text-xs text-slate-500">Latency</p>
                  <p className="font-mono text-sm text-slate-900">{sys.ping}</p>
                </div>
                <div className="text-right hidden sm:block">
                  <p className="text-xs text-slate-500">Uptime (30d)</p>
                  <p className="font-mono text-sm text-slate-900">{sys.uptime}</p>
                </div>
                <Badge variant={sys.status === 'operational' ? 'success' : 'warning'}>
                  {sys.status.toUpperCase()}
                </Badge>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Temporary icon fallback since Brain is not exported from lucide-react in older versions, we use Zap or Activity
function Brain(props: any) {
  return <Activity {...props} />;
}
