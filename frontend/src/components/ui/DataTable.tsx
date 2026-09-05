import { type ReactNode } from 'react';
import { cn } from '../../utils';

interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (item: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (item: T) => void;
  className?: string;
  isLoading?: boolean;
}

export function DataTable<T>({ data, columns, onRowClick, className, isLoading }: DataTableProps<T>) {
  return (
    <div className={cn("w-full overflow-auto rounded-lg border border-slate-200/60 bg-white", className)}>
      <table className="w-full caption-bottom text-sm whitespace-nowrap">
        <thead className="[&_tr]:border-b bg-slate-50/50">
          <tr className="border-b transition-colors hover:bg-slate-100/50 data-[state=selected]:bg-slate-100">
            {columns.map((col, index) => (
              <th
                key={index}
                className={cn("h-11 px-4 text-left align-middle font-semibold text-slate-500 text-xs tracking-wider uppercase", col.className)}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="[&_tr:last-child]:border-0">
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="h-32 text-center">
                <div className="flex flex-col items-center justify-center space-y-3 text-slate-400">
                  <div className="w-6 h-6 border-2 border-slate-300 border-t-brand-500 rounded-full animate-spin" />
                  <span className="text-sm">Loading data...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="h-32 text-center">
                <div className="flex flex-col items-center justify-center space-y-2 text-slate-500">
                  <div className="text-sm bg-slate-100 px-3 py-1 rounded-full font-medium">No results found</div>
                  <p className="text-xs text-slate-400">There is no data to display for this view.</p>
                </div>
              </td>
            </tr>
          ) : (
            data.map((item, rowIndex) => (
              <tr
                key={rowIndex}
                onClick={() => onRowClick && onRowClick(item)}
                className={cn(
                  "border-b transition-colors hover:bg-slate-50/50 data-[state=selected]:bg-slate-100",
                  onRowClick && "cursor-pointer"
                )}
              >
                {columns.map((col, colIndex) => (
                  <td key={colIndex} className={cn("p-4 align-middle text-slate-900", col.className)}>
                    {col.cell ? col.cell(item) : col.accessorKey ? String(item[col.accessorKey]) : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
