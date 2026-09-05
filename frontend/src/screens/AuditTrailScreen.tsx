import { MOCK_AUDIT, type AuditEvent } from '../data/mock';
import { DataTable } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { ScrollText, FileText } from 'lucide-react';
import { Button } from '../components/ui/Button';

export function AuditTrailScreen() {
  const columns = [
    {
      header: 'Timestamp',
      cell: (item: AuditEvent) => (
        <span className="font-mono text-xs text-slate-500">
          {new Date(item.timestamp).toLocaleString()}
        </span>
      ),
      className: 'w-[180px]'
    },
    {
      header: 'Event Type',
      cell: (item: AuditEvent) => {
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
      accessorKey: 'actor' as keyof AuditEvent,
      className: 'font-medium w-[180px]'
    },
    {
      header: 'Details',
      accessorKey: 'details' as keyof AuditEvent,
      className: 'text-slate-600'
    }
  ];

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
        <DataTable data={MOCK_AUDIT} columns={columns} />
      </div>
    </div>
  );
}
