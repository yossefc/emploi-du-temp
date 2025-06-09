import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { 
  ChevronUpIcon, 
  ChevronDownIcon, 
  FunnelIcon,
  ArrowsPointingOutIcon,
  ArrowDownTrayIcon,
  Cog6ToothIcon,
  XMarkIcon,
  CheckIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';
import { useTable } from '../../hooks/useTable';

export interface ColumnConfig<T = any> {
  key: string;
  title: string;
  dataIndex: keyof T;
  sortable?: boolean;
  filterable?: boolean;
  filterType?: 'text' | 'select' | 'date' | 'number' | 'boolean';
  filterOptions?: Array<{ label: string; value: any }>;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  width?: number | string;
  minWidth?: number;
  align?: 'left' | 'center' | 'right';
  fixed?: 'left' | 'right';
  resizable?: boolean;
  hidden?: boolean;
  exportable?: boolean;
}

export interface DataTableProps<T = any> {
  data: T[];
  columns: ColumnConfig<T>[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    showSizeChanger?: boolean;
    pageSizeOptions?: string[];
    onChange: (page: number, pageSize: number) => void;
  };
  rowSelection?: {
    type: 'checkbox' | 'radio';
    selectedRowKeys: React.Key[];
    onChange: (selectedRowKeys: React.Key[], selectedRows: T[]) => void;
    getCheckboxProps?: (record: T) => any;
  };
  rowKey?: keyof T | ((record: T) => React.Key);
  size?: 'small' | 'medium' | 'large';
  bordered?: boolean;
  showHeader?: boolean;
  scroll?: { x?: number | string; y?: number | string };
  expandable?: {
    expandedRowRender: (record: T, index: number) => React.ReactNode;
    rowExpandable?: (record: T) => boolean;
  };
  onRow?: (record: T, index: number) => any;
  className?: string;
  title?: string;
  actions?: Array<{
    key: string;
    label: string;
    icon?: React.ReactNode;
    onClick: (selectedRows: T[]) => void;
    disabled?: boolean;
    type?: 'primary' | 'secondary' | 'danger';
  }>;
  exportConfig?: {
    filename?: string;
    formats?: Array<'csv' | 'excel' | 'pdf'>;
    onExport?: (format: string, data: T[]) => void;
  };
  persistState?: boolean;
  stateKey?: string;
}

export default function DataTable<T extends Record<string, any>>({
  data,
  columns: initialColumns,
  loading = false,
  pagination,
  rowSelection,
  rowKey = 'id',
  size = 'medium',
  bordered = true,
  showHeader = true,
  scroll,
  expandable,
  onRow,
  className = '',
  title,
  actions = [],
  exportConfig,
  persistState = true,
  stateKey = 'dataTable'
}: DataTableProps<T>) {
  const tableRef = useRef<HTMLDivElement>(null);
  
  const {
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
  } = useTable<T>({
    data,
    columns: initialColumns,
    rowSelection,
    rowKey,
    persistState,
    stateKey
  });

  const [showColumnSettings, setShowColumnSettings] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizingColumn, setResizingColumn] = useState<string | null>(null);

  // Load saved state on mount
  useEffect(() => {
    if (persistState) {
      loadState();
    }
  }, [persistState, loadState]);

  // Save state when it changes
  useEffect(() => {
    if (persistState) {
      saveState();
    }
  }, [sortConfig, filters, columnWidths, columnOrder, hiddenColumns, persistState, saveState]);

  const visibleColumns = useMemo(() => {
    return columnOrder
      .map(key => initialColumns.find(col => col.key === key))
      .filter((col): col is ColumnConfig<T> => col !== undefined && !hiddenColumns.includes(col.key));
  }, [initialColumns, columnOrder, hiddenColumns]);

  const getRowKey = useCallback((record: T, index: number): React.Key => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey] ?? index;
  }, [rowKey]);

  const handleRowSelect = useCallback((record: T, selected: boolean) => {
    if (!rowSelection) return;
    
    const recordKey = getRowKey(record, 0);
    let newSelectedKeys: React.Key[];
    
    if (rowSelection.type === 'radio') {
      newSelectedKeys = selected ? [recordKey] : [];
    } else {
      if (selected) {
        newSelectedKeys = [...rowSelection.selectedRowKeys, recordKey];
      } else {
        newSelectedKeys = rowSelection.selectedRowKeys.filter(key => key !== recordKey);
      }
    }
    
    const newSelectedRows = data.filter(item => 
      newSelectedKeys.includes(getRowKey(item, 0))
    );
    
    rowSelection.onChange(newSelectedKeys, newSelectedRows);
  }, [rowSelection, data, getRowKey]);

  const handleSelectAll = useCallback((selected: boolean) => {
    if (!rowSelection || rowSelection.type === 'radio') return;
    
    if (selected) {
      const allKeys = tableData.map((record, index) => getRowKey(record, index));
      rowSelection.onChange(allKeys, [...tableData]);
    } else {
      rowSelection.onChange([], []);
    }
  }, [rowSelection, tableData, getRowKey]);

  const isRowSelected = useCallback((record: T, index: number): boolean => {
    if (!rowSelection) return false;
    const recordKey = getRowKey(record, index);
    return rowSelection.selectedRowKeys.includes(recordKey);
  }, [rowSelection, getRowKey]);

  const allRowsSelected = useMemo(() => {
    if (!rowSelection || tableData.length === 0) return false;
    return tableData.every((record, index) => isRowSelected(record, index));
  }, [rowSelection, tableData, isRowSelected]);

  const someRowsSelected = useMemo(() => {
    if (!rowSelection) return false;
    return rowSelection.selectedRowKeys.length > 0 && !allRowsSelected;
  }, [rowSelection, allRowsSelected]);

  const handleExport = useCallback((format: 'csv' | 'excel' | 'pdf') => {
    if (exportConfig?.onExport) {
      exportConfig.onExport(format, selectedRows.length > 0 ? selectedRows : tableData);
    } else {
      exportData(format, selectedRows.length > 0 ? selectedRows : tableData, {
        filename: exportConfig?.filename,
        columns: visibleColumns
      });
    }
  }, [exportConfig, exportData, selectedRows, tableData, visibleColumns]);

  const renderFilterInput = useCallback((column: ColumnConfig<T>) => {
    const value = filters[column.key] || '';
    
    switch (column.filterType) {
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleFilter(column.key, e.target.value)}
            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:border-indigo-500"
          >
            <option value="">Tous</option>
            {column.filterOptions?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleFilter(column.key, e.target.value)}
            placeholder="Filtrer..."
            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:border-indigo-500"
          />
        );
      
      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => handleFilter(column.key, e.target.value)}
            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:border-indigo-500"
          />
        );
      
      case 'boolean':
        return (
          <select
            value={value}
            onChange={(e) => handleFilter(column.key, e.target.value)}
            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:border-indigo-500"
          >
            <option value="">Tous</option>
            <option value="true">Oui</option>
            <option value="false">Non</option>
          </select>
        );
      
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFilter(column.key, e.target.value)}
            placeholder="Filtrer..."
            className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:border-indigo-500"
          />
        );
    }
  }, [filters, handleFilter]);

  const hasActiveFilters = useMemo(() => {
    return Object.values(filters).some(value => value !== '' && value !== null && value !== undefined);
  }, [filters]);

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      {(title || actions.length > 0 || exportConfig) && (
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {title && <h3 className="text-lg font-medium text-gray-900">{title}</h3>}
              
              {/* Bulk Actions */}
              {actions.length > 0 && selectedRows.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    {selectedRows.length} élément(s) sélectionné(s)
                  </span>
                  {actions.map(action => (
                    <button
                      key={action.key}
                      onClick={() => action.onClick(selectedRows)}
                      disabled={action.disabled}
                      className={`
                        inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md
                        ${action.type === 'danger' 
                          ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                          : action.type === 'primary'
                          ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }
                        disabled:opacity-50 disabled:cursor-not-allowed
                      `}
                    >
                      {action.icon && <span className="mr-1">{action.icon}</span>}
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* Filter Reset */}
              {hasActiveFilters && (
                <button
                  onClick={resetFilters}
                  className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-gray-900"
                >
                  <XMarkIcon className="w-4 h-4 mr-1" />
                  Réinitialiser filtres
                </button>
              )}

              {/* Export */}
              {exportConfig && (
                <div className="relative">
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        handleExport(e.target.value as any);
                        e.target.value = '';
                      }
                    }}
                    className="appearance-none bg-white border border-gray-300 rounded-md px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Exporter</option>
                    {exportConfig.formats?.includes('csv') && <option value="csv">CSV</option>}
                    {exportConfig.formats?.includes('excel') && <option value="excel">Excel</option>}
                    {exportConfig.formats?.includes('pdf') && <option value="pdf">PDF</option>}
                  </select>
                  <ArrowDownTrayIcon className="w-4 h-4 absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none text-gray-400" />
                </div>
              )}

              {/* Column Settings */}
              <button
                onClick={() => setShowColumnSettings(!showColumnSettings)}
                className="inline-flex items-center px-2 py-1.5 border border-gray-300 rounded-md text-xs text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:border-indigo-500"
              >
                <AdjustmentsHorizontalIcon className="w-4 h-4 mr-1" />
                Colonnes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Column Settings Panel */}
      {showColumnSettings && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-3 gap-4">
            {initialColumns.map(column => (
              <label key={column.key} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={!hiddenColumns.includes(column.key)}
                  onChange={(e) => toggleColumnVisibility(column.key, !e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">{column.title}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Table Container */}
      <div 
        ref={tableRef}
        className="overflow-auto"
        style={{ maxHeight: scroll?.y }}
      >
        <table className="min-w-full divide-y divide-gray-200">
          {/* Header */}
          {showHeader && (
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                {/* Selection Column */}
                {rowSelection && (
                  <th className="w-12 px-3 py-3 text-left">
                    {rowSelection.type === 'checkbox' && (
                      <input
                        type="checkbox"
                        checked={allRowsSelected}
                        ref={(input) => {
                          if (input) input.indeterminate = someRowsSelected;
                        }}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                    )}
                  </th>
                )}

                {/* Data Columns */}
                {visibleColumns.map((column) => (
                  <th
                    key={column.key}
                    className={`
                      px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider
                      ${column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''}
                      ${bordered ? 'border-r border-gray-200 last:border-r-0' : ''}
                    `}
                    style={{ 
                      width: columnWidths[column.key] || column.width,
                      minWidth: column.minWidth,
                      textAlign: column.align || 'left'
                    }}
                    onClick={() => column.sortable && handleSort(column.key)}
                  >
                    <div className="flex items-center justify-between">
                      <span>{column.title}</span>
                      <div className="flex items-center space-x-1">
                        {column.sortable && (
                          <div className="flex flex-col">
                            <ChevronUpIcon 
                              className={`w-3 h-3 ${
                                sortConfig?.key === column.key && sortConfig.direction === 'asc'
                                  ? 'text-indigo-600' 
                                  : 'text-gray-400'
                              }`}
                            />
                            <ChevronDownIcon 
                              className={`w-3 h-3 -mt-1 ${
                                sortConfig?.key === column.key && sortConfig.direction === 'desc'
                                  ? 'text-indigo-600' 
                                  : 'text-gray-400'
                              }`}
                            />
                          </div>
                        )}
                        {column.filterable && (
                          <FunnelIcon 
                            className={`w-3 h-3 ${
                              filters[column.key] ? 'text-indigo-600' : 'text-gray-400'
                            }`}
                          />
                        )}
                      </div>
                    </div>
                  </th>
                ))}
              </tr>

              {/* Filter Row */}
              <tr className="bg-white">
                {rowSelection && <th className="px-3 py-2"></th>}
                {visibleColumns.map((column) => (
                  <th key={`filter-${column.key}`} className="px-3 py-2">
                    {column.filterable && renderFilterInput(column)}
                  </th>
                ))}
              </tr>
            </thead>
          )}

          {/* Body */}
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              // Loading Skeleton
              Array.from({ length: pagination?.pageSize || 10 }).map((_, index) => (
                <tr key={`skeleton-${index}`}>
                  {rowSelection && (
                    <td className="px-3 py-4">
                      <div className="h-4 w-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                  )}
                  {visibleColumns.map((column) => (
                    <td key={`skeleton-${column.key}`} className="px-3 py-4">
                      <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                    </td>
                  ))}
                </tr>
              ))
            ) : tableData.length === 0 ? (
              // Empty State
              <tr>
                <td 
                  colSpan={visibleColumns.length + (rowSelection ? 1 : 0)}
                  className="px-3 py-12 text-center text-gray-500"
                >
                  <div className="flex flex-col items-center">
                    <FunnelIcon className="w-12 h-12 text-gray-300 mb-4" />
                    <p className="text-lg font-medium">Aucune donnée trouvée</p>
                    <p className="text-sm">Essayez d'ajuster vos filtres ou d'ajouter de nouvelles données</p>
                  </div>
                </td>
              </tr>
            ) : (
              // Data Rows
              tableData.map((record, index) => (
                <tr
                  key={getRowKey(record, index)}
                  className={`
                    hover:bg-gray-50 transition-colors duration-150
                    ${isRowSelected(record, index) ? 'bg-indigo-50' : ''}
                  `}
                  {...(onRow ? onRow(record, index) : {})}
                >
                  {/* Selection Cell */}
                  {rowSelection && (
                    <td className="px-3 py-4">
                      <input
                        type={rowSelection.type}
                        checked={isRowSelected(record, index)}
                        onChange={(e) => handleRowSelect(record, e.target.checked)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        {...(rowSelection.getCheckboxProps ? rowSelection.getCheckboxProps(record) : {})}
                      />
                    </td>
                  )}

                  {/* Data Cells */}
                  {visibleColumns.map((column) => (
                    <td
                      key={column.key}
                      className={`
                        px-3 py-4 text-sm text-gray-900
                        ${bordered ? 'border-r border-gray-200 last:border-r-0' : ''}
                      `}
                      style={{ textAlign: column.align || 'left' }}
                    >
                      {column.render 
                        ? column.render(record[column.dataIndex], record, index)
                        : record[column.dataIndex]
                      }
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">
              Affichage de {Math.min((pagination.current - 1) * pagination.pageSize + 1, pagination.total)} à{' '}
              {Math.min(pagination.current * pagination.pageSize, pagination.total)} sur {pagination.total} éléments
            </span>
            
            {pagination.showSizeChanger && (
              <select
                value={pagination.pageSize}
                onChange={(e) => pagination.onChange(1, parseInt(e.target.value))}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                {(pagination.pageSizeOptions || ['10', '25', '50', '100']).map(size => (
                  <option key={size} value={size}>{size} / page</option>
                ))}
              </select>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => pagination.onChange(pagination.current - 1, pagination.pageSize)}
              disabled={pagination.current <= 1}
              className="px-3 py-1 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Précédent
            </button>
            
            {/* Page Numbers */}
            {Array.from({ length: Math.ceil(pagination.total / pagination.pageSize) }, (_, index) => {
              const page = index + 1;
              const isCurrentPage = page === pagination.current;
              const showPage = Math.abs(page - pagination.current) <= 2 || page === 1 || page === Math.ceil(pagination.total / pagination.pageSize);
              
              if (!showPage) {
                if (page === pagination.current - 3 || page === pagination.current + 3) {
                  return <span key={page} className="px-2 text-gray-500">...</span>;
                }
                return null;
              }
              
              return (
                <button
                  key={page}
                  onClick={() => pagination.onChange(page, pagination.pageSize)}
                  className={`
                    px-3 py-1 border rounded text-sm
                    ${isCurrentPage 
                      ? 'bg-indigo-600 text-white border-indigo-600' 
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }
                  `}
                >
                  {page}
                </button>
              );
            })}
            
            <button
              onClick={() => pagination.onChange(pagination.current + 1, pagination.pageSize)}
              disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
              className="px-3 py-1 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Suivant
            </button>
          </div>
        </div>
      )}
    </div>
  );
}