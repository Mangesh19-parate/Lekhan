import React, { useState, useMemo } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { Skeleton } from "./Skeleton";
import { EmptyState } from "./EmptyState";
import { Button } from "./Button";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
  align?: "left" | "center" | "right";
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string | number;
  sortKey?: string;
  sortDirection?: "asc" | "desc";
  onSort?: (key: string) => void;
  isLoading?: boolean;
  emptyMessage?: string;
  emptyAction?: React.ReactNode;
  enablePagination?: boolean;
  pageSize?: number;
  pageSizeOptions?: number[];
  enableSearch?: boolean;
  searchPlaceholder?: string;
  filterComponent?: React.ReactNode;
  className?: string;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  sortKey: controlledSortKey,
  sortDirection: controlledSortDir,
  onSort: controlledOnSort,
  isLoading = false,
  emptyMessage = "No records found.",
  emptyAction,
  enablePagination = true,
  pageSize: initialPageSize = 10,
  pageSizeOptions = [10, 25, 50],
  enableSearch = false,
  searchPlaceholder = "Search records...",
  filterComponent,
  className = "",
}: TableProps<T>) {
  // Internal sort state if not controlled
  const [internalSortKey, setInternalSortKey] = useState<string | undefined>(undefined);
  const [internalSortDir, setInternalSortDir] = useState<"asc" | "desc">("asc");

  const sortKey = controlledSortKey ?? internalSortKey;
  const sortDirection = controlledSortDir ?? internalSortDir;

  // Search & Pagination state
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const handleSort = (key: string) => {
    if (controlledOnSort) {
      controlledOnSort(key);
    } else {
      if (internalSortKey === key) {
        setInternalSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
      } else {
        setInternalSortKey(key);
        setInternalSortDir("asc");
      }
    }
    setCurrentPage(1);
  };

  // Filter by search query
  const filteredData = useMemo(() => {
    if (!enableSearch || !searchQuery.trim()) return data;
    const q = searchQuery.toLowerCase().trim();
    return data.filter((row) => {
      return columns.some((col) => {
        const val = (row as Record<string, unknown>)[col.key];
        return val != null && String(val).toLowerCase().includes(q);
      });
    });
  }, [data, searchQuery, enableSearch, columns]);

  // Sort data if using internal sorting
  const sortedData = useMemo(() => {
    if (!sortKey || controlledOnSort) return filteredData;
    return [...filteredData].sort((a, b) => {
      const valA = (a as Record<string, unknown>)[sortKey];
      const valB = (b as Record<string, unknown>)[sortKey];
      if (valA == null && valB == null) return 0;
      if (valA == null) return sortDirection === "asc" ? 1 : -1;
      if (valB == null) return sortDirection === "asc" ? -1 : 1;

      if (typeof valA === "number" && typeof valB === "number") {
        return sortDirection === "asc" ? valA - valB : valB - valA;
      }
      return sortDirection === "asc"
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredData, sortKey, sortDirection, controlledOnSort]);

  // Pagination calculation
  const totalItems = sortedData.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safeCurrentPage = Math.min(currentPage, totalPages);

  const paginatedData = useMemo(() => {
    if (!enablePagination) return sortedData;
    const start = (safeCurrentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, enablePagination, safeCurrentPage, pageSize]);

  return (
    <div className={`flex flex-col gap-3 w-full ${className}`}>
      {/* Top Filter & Search Bar */}
      {(enableSearch || filterComponent) && (
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {enableSearch && (
            <div className="relative flex-1 max-w-sm">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-tertiary">
                <Search size={15} />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder={searchPlaceholder}
                className="w-full h-9 pl-9 pr-3 rounded-input border border-line-subtle bg-subtle dark:bg-sunken/40 text-xs font-ui focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-text-primary"
              />
            </div>
          )}
          {filterComponent && <div className="flex items-center gap-2">{filterComponent}</div>}
        </div>
      )}

      {/* Main Table Container */}
      <div className="w-full overflow-x-auto border border-line-subtle rounded-card bg-card shadow-card">
        <table className="w-full border-collapse text-left text-sm font-ui">
          <thead>
            <tr className="bg-sunken border-b border-line-medium sticky top-0 z-10 select-none">
              {columns.map((col) => {
                const isSorted = sortKey === col.key;
                return (
                  <th
                    key={col.key}
                    aria-sort={
                      col.sortable
                        ? isSorted
                          ? sortDirection === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                        : undefined
                    }
                    className={`py-3 px-4 font-semibold text-text-secondary text-xs tracking-wider uppercase ${
                      col.sortable ? "cursor-pointer hover:text-text-primary" : ""
                    }`}
                    style={{ width: col.width, textAlign: col.align || "left" }}
                    onClick={() => col.sortable && handleSort(col.key)}
                  >
                    <div
                      className={`inline-flex items-center gap-1.5 ${
                        col.align === "right"
                          ? "justify-end"
                          : col.align === "center"
                          ? "justify-center"
                          : "justify-start"
                      }`}
                    >
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className="shrink-0 text-text-tertiary">
                          {isSorted ? (
                            sortDirection === "asc" ? (
                              <ArrowUp size={13} className="text-brand-600 dark:text-brand-400" />
                            ) : (
                              <ArrowDown size={13} className="text-brand-600 dark:text-brand-400" />
                            )
                          ) : (
                            <ArrowUpDown size={13} />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, rIdx) => (
                <tr key={`skeleton-${rIdx}`} className="border-b border-line-subtle">
                  {columns.map((col, cIdx) => (
                    <td key={`cell-${rIdx}-${cIdx}`} className="py-3.5 px-4">
                      <Skeleton height="18px" width={cIdx === 0 ? "80%" : "60%"} />
                    </td>
                  ))}
                </tr>
              ))
            ) : paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="py-10 px-4 text-center">
                  <EmptyState
                    title={emptyMessage}
                    description={
                      searchQuery
                        ? "Try adjusting your search criteria or clearing filters."
                        : "No data is currently available in this registry."
                    }
                    action={emptyAction}
                  />
                </td>
              </tr>
            ) : (
              paginatedData.map((row) => (
                <tr
                  key={keyExtractor(row)}
                  className="border-b border-line-subtle hover:bg-brand-50/50 dark:hover:bg-brand-900/20 transition-colors duration-100"
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className="py-3 px-4 text-text-primary text-sm align-middle"
                      style={{ textAlign: col.align || "left" }}
                    >
                      {col.render
                        ? col.render(row)
                        : String((row as Record<string, unknown>)[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {enablePagination && totalItems > 0 && !isLoading && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-1 py-1 text-xs text-text-secondary font-ui">
          <div className="flex items-center gap-2">
            <span>
              Showing{" "}
              <strong className="text-text-primary font-semibold">
                {(safeCurrentPage - 1) * pageSize + 1}
              </strong>{" "}
              to{" "}
              <strong className="text-text-primary font-semibold">
                {Math.min(safeCurrentPage * pageSize, totalItems)}
              </strong>{" "}
              of <strong className="text-text-primary font-semibold">{totalItems}</strong> entries
            </span>
            <div className="flex items-center gap-1 ml-3">
              <span>Per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="h-7 px-2 border border-line-subtle rounded-input bg-card text-text-primary text-xs focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                {pageSizeOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant="secondary"
              size="sm"
              disabled={safeCurrentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="h-7 px-2.5 text-xs"
            >
              <ChevronLeft size={14} className="mr-0.5" />
              Prev
            </Button>
            <span className="px-2 font-medium text-text-primary">
              Page {safeCurrentPage} of {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              disabled={safeCurrentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="h-7 px-2.5 text-xs"
            >
              Next
              <ChevronRight size={14} className="ml-0.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
