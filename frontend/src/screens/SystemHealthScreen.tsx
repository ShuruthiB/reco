import { Card } from '../components/ui/Card';
import { Activity, Database, Server, Webhook, Zap } from 'lucide-react';
import { Badge } from '../components/ui/Badge';

export function SystemHealthScreen() {
  const systems = [
    { name: 'API Gateway', status: 'operational', uptime: '99.99%', ping: '45ms', icon: Server },
    { name: 'Database / Storage', status: 'operational', uptime: '100%', ping: '12ms', icon: Database },
    { name: 'ML Scoring Engine', status: 'operational', uptime: '99.95%', ping: '85ms', icon: Brain },
    { name: 'Razorpay Webhooks', status: 'degraded', uptime: '98.50%', ping: '120ms', icon: Webhook, message: 'Elevated latency observed on webhook ingestion.' },
    { name: 'Execution Workers', status: 'operational', uptime: '99.99%', ping: '20ms', icon: Zap },
  ];

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
