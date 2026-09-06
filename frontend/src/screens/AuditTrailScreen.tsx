import { useState, useEffect } from 'react';
import { DataTable } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { ScrollText, FileText, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/Button';

export function AuditTrailScreen() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/audit?page=1&page_size=100')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
        return res.json();
      })
      .then(data => {
        setEvents(data.items || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setEvents([]);
        setLoading(false);
      });
  }, []);
  const columns = [
    {
      header: 'Timestamp',
      cell: (item: any) => (
        <span className="font-mono text-xs text-slate-500">
          {new Date(item.timestamp).toLocaleString()}
        </span>
      ),
      className: 'w-[180px]'
    },
    {
      header: 'Event Type',
      cell: (item: any) => {
        let variant: 'default' | 'success' | 'neutral' | 'warning' = 'neutral';
        if (item.type.includes('EXECUTED')) variant = 'success';
        if (item.type.includes('POLICY') || item.type.includes('BUDGET')) variant = 'warning';
        
        return (
          <Badge variant={variant} className="font-mono text-[10px]">
            {item.type}
          </Badge>
        );
      },
      className: 'w-[200px]'
    },
    {
      header: 'Actor',
      accessorKey: 'actor',
      className: 'font-medium w-[180px]'
    },
    {
      header: 'Details',
      accessorKey: 'details',
      className: 'text-slate-600'
    }
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
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Audit Trail</h1>
          <p className="text-sm text-slate-500">Immutable, append-only log of domain events.</p>
        </div>
        <Button variant="outline">
          <FileText className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center bg-slate-50 gap-2">
          <ScrollText className="w-4 h-4 text-slate-500" />
          <h3 className="font-semibold text-sm text-slate-700">Domain Event Log</h3>
        </div>
        <DataTable data={events} columns={columns} />
      </div>
    </div>
  );
}
