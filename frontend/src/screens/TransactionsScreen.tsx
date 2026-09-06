import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataTable } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { Loader2 } from 'lucide-react';

export function TransactionsScreen() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/transactions?page=1&page_size=50')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        setTransactions(data.items || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching transactions:", err);
        setTransactions([]);
        setLoading(false);
      });
  }, []);

  const columns = [
    {
      header: 'Transaction ID',
      accessorKey: 'id',
      className: 'font-medium',
    },
    {
      header: 'Customer',
      cell: (item: any) => (
        <div>
          <div className="font-medium text-slate-900">{item.customer_name || 'Anonymous'}</div>
          <div className="text-xs text-slate-500">{item.customer_email || 'No email'}</div>
        </div>
      ),
    },
    {
      header: 'Amount',
      className: 'text-right',
      cell: (item: any) => (
        <span className="font-medium numeric-data text-blue-600">
          ${Number(item.amount).toFixed(2)}
        </span>
      ),
    },
    {
      header: 'Status',
      cell: (item: any) => {
        const variants: Record<string, "success" | "warning" | "danger" | "default" | "neutral"> = {
          pending: 'warning',
          recovered: 'success',
          failed: 'danger',
          quarantined: 'neutral',
          abandoned: 'neutral',
          success: 'success'
        };
        return (
          <Badge variant={variants[item.status] || 'default'}>
            {item.status.toUpperCase()}
          </Badge>
        );
      },
    },
    {
      header: 'Risk',
      cell: (item: any) => {
        const risk = item.risk_level || 'low';
        const variants: Record<string, "danger" | "warning" | "default"> = {
          high: 'danger',
          medium: 'warning',
          low: 'default'
        };
        return (
          <Badge variant={variants[risk] || 'default'}>
            {risk.toUpperCase()}
          </Badge>
        );
      },
    },
    {
      header: 'Date',
      cell: (item: any) => (
        <span className="text-slate-500">
          {new Date(item.created_at).toLocaleDateString()}
        </span>
      ),
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
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Transactions</h1>
          <p className="text-sm text-slate-500">Manage and monitor payment attempts and recoveries.</p>
        </div>
      </div>
      
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <h3 className="font-semibold text-sm text-slate-700">Recent Transactions</h3>
        </div>
        <DataTable 
          data={transactions} 
          columns={columns} 
          onRowClick={(item: any) => navigate(`/transactions/${item.id}`)}
        />
      </div>
    </div>
  );
}
