import { useState, useCallback, useMemo, useEffect } from 'react';
import { ColumnConfig } from '../components/Common/DataTable';

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

export interface TableState {
  sortConfig: SortConfig | null;
  filters: Record<string, any>;
  columnWidths: Record<string, number>;
  columnOrder: string[];
  hiddenColumns: string[];
  selectedRows: any[];
}

export interface UseTableOptions<T> {
  data: T[];
  columns: ColumnConfig<T>[];
  rowSelection?: {
    type: 'checkbox' | 'radio';
    selectedRowKeys: React.Key[];
    onChange: (selectedRowKeys: React.Key[], selectedRows: T[]) => void;
  };
  rowKey?: keyof T | ((record: T) => React.Key);
  persistState?: boolean;
  stateKey?: string;
}

export function useTable<T extends Record<string, any>>({
  data,
  columns,
  rowSelection,
  rowKey = 'id',
  persistState = true,
  stateKey = 'dataTable'
}: UseTableOptions<T>) {
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [columnOrder, setColumnOrder] = useState<string[]>(() => 
    columns.map(col => col.key)
  );
  const [hiddenColumns, setHiddenColumns] = useState<string[]>([]);

  // Get selected rows from rowSelection prop
  const selectedRows = useMemo(() => {
    if (!rowSelection) return [];
    
    return data.filter(item => {
      const itemKey = typeof rowKey === 'function' 
        ? rowKey(item) 
        : item[rowKey];
      return rowSelection.selectedRowKeys.includes(itemKey);
    });
  }, [data, rowSelection, rowKey]);

  // Sort and filter data
  const tableData = useMemo(() => {
    let processedData = [...data];

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value === '' || value === null || value === undefined) return;
      
      const column = columns.find(col => col.key === key);
      if (!column) return;

      processedData = processedData.filter(item => {
        const itemValue = item[column.dataIndex];
        
        switch (column.filterType) {
          case 'text':
            return String(itemValue).toLowerCase().includes(String(value).toLowerCase());
          
          case 'number':
            return Number(itemValue) === Number(value);
          
          case 'select':
            return itemValue === value;
          
          case 'date':
            const itemDate = new Date(itemValue).toISOString().split('T')[0];
            return itemDate === value;
          
          case 'boolean':
            return String(itemValue) === value;
          
          default:
            return String(itemValue).toLowerCase().includes(String(value).toLowerCase());
        }
      });
    });

    // Apply sorting
    if (sortConfig) {
      const column = columns.find(col => col.key === sortConfig.key);
      if (column) {
        processedData.sort((a, b) => {
          const aValue = a[column.dataIndex];
          const bValue = b[column.dataIndex];
          
          let comparison = 0;
          
          if (aValue < bValue) {
            comparison = -1;
          } else if (aValue > bValue) {
            comparison = 1;
          }
          
          return sortConfig.direction === 'desc' ? comparison * -1 : comparison;
        });
      }
    }

    return processedData;
  }, [data, filters, sortConfig, columns]);

  // Handle sorting
  const handleSort = useCallback((key: string) => {
    setSortConfig(current => {
      if (current?.key === key) {
        if (current.direction === 'asc') {
          return { key, direction: 'desc' };
        } else {
          return null; // Remove sorting
        }
      }
      return { key, direction: 'asc' };
    });
  }, []);

  // Handle filtering
  const handleFilter = useCallback((key: string, value: any) => {
    setFilters(current => ({
      ...current,
      [key]: value
    }));
  }, []);

  // Reset filters
  const resetFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Handle column resize
  const handleColumnResize = useCallback((key: string, width: number) => {
    setColumnWidths(current => ({
      ...current,
      [key]: width
    }));
  }, []);

  // Handle column reorder
  const handleColumnReorder = useCallback((fromIndex: number, toIndex: number) => {
    setColumnOrder(current => {
      const newOrder = [...current];
      const [removed] = newOrder.splice(fromIndex, 1);
      newOrder.splice(toIndex, 0, removed);
      return newOrder;
    });
  }, []);

  // Toggle column visibility
  const toggleColumnVisibility = useCallback((key: string, hidden: boolean) => {
    setHiddenColumns(current => {
      if (hidden) {
        return [...current, key];
      } else {
        return current.filter(col => col !== key);
      }
    });
  }, []);

  // Export data
  const exportData = useCallback((
    format: 'csv' | 'excel' | 'pdf',
    exportData: T[],
    options?: {
      filename?: string;
      columns?: ColumnConfig<T>[];
    }
  ) => {
    const filename = options?.filename || `export_${new Date().toISOString().split('T')[0]}`;
    const exportColumns = options?.columns || columns.filter(col => col.exportable !== false);

    switch (format) {
      case 'csv':
        exportToCSV(exportData, exportColumns, filename);
        break;
      case 'excel':
        exportToExcel(exportData, exportColumns, filename);
        break;
      case 'pdf':
        exportToPDF(exportData, exportColumns, filename);
        break;
    }
  }, [columns]);

  // Save state to localStorage
  const saveState = useCallback(() => {
    if (!persistState) return;
    
    const state: TableState = {
      sortConfig,
      filters,
      columnWidths,
      columnOrder,
      hiddenColumns,
      selectedRows
    };
    
    localStorage.setItem(`table_${stateKey}`, JSON.stringify(state));
  }, [sortConfig, filters, columnWidths, columnOrder, hiddenColumns, selectedRows, persistState, stateKey]);

  // Load state from localStorage
  const loadState = useCallback(() => {
    if (!persistState) return;
    
    try {
      const savedState = localStorage.getItem(`table_${stateKey}`);
      if (savedState) {
        const state: TableState = JSON.parse(savedState);
        setSortConfig(state.sortConfig);
        setFilters(state.filters || {});
        setColumnWidths(state.columnWidths || {});
        setColumnOrder(state.columnOrder || columns.map(col => col.key));
        setHiddenColumns(state.hiddenColumns || []);
      }
    } catch (error) {
      console.warn('Failed to load table state:', error);
    }
  }, [persistState, stateKey, columns]);

  return {
    tableData,
    sortConfig,
    filters,
    selectedRows,
    columnWidths,
    columnOrder,
    hiddenColumns,
    handleSort,
    handleFilter,
    handleColumnResize,
    handleColumnReorder,
    toggleColumnVisibility,
    exportData,
    resetFilters,
    saveState,
    loadState
  };
}

// Helper functions for export
function exportToCSV<T>(data: T[], columns: ColumnConfig<T>[], filename: string) {
  const headers = columns.map(col => col.title).join(',');
  const rows = data.map(item => 
    columns.map(col => {
      const value = item[col.dataIndex];
      // Escape commas and quotes
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    }).join(',')
  );
  
  const csv = [headers, ...rows].join('\n');
  downloadFile(csv, `${filename}.csv`, 'text/csv');
}

function exportToExcel<T>(data: T[], columns: ColumnConfig<T>[], filename: string) {
  // For now, export as CSV (would need xlsx library for real Excel format)
  exportToCSV(data, columns, filename);
}

function exportToPDF<T>(data: T[], columns: ColumnConfig<T>[], filename: string) {
  // For now, export as CSV (would need pdf library like jsPDF for real PDF)
  exportToCSV(data, columns, filename);
}

function downloadFile(content: string, filename: string, contentType: string) {
  const blob = new Blob([content], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}