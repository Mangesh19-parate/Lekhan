import React from "react";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

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
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  sortKey,
  sortDirection,
  onSort,
  isLoading = false,
  emptyMessage = "No records found.",
}: TableProps<T>) {
  return (
    <div
      style={{
        width: "100%",
        overflowX: "auto",
        border: "1px solid var(--line-subtle)",
        borderRadius: "var(--radius-card)",
        backgroundColor: "var(--surface-card)",
      }}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "0.875rem",
          textAlign: "left",
        }}
      >
        <thead>
          <tr
            style={{
              backgroundColor: "var(--surface-sunken)",
              borderBottom: "1px solid var(--line-medium)",
              position: "sticky",
              top: 0,
              zIndex: 10,
            }}
          >
            {columns.map((col) => {
              const isSorted = sortKey === col.key;
              return (
                <th
                  key={col.key}
                  aria-sort={col.sortable ? (isSorted ? (sortDirection === "asc" ? "ascending" : "descending") : "none") : undefined}
                  style={{
                    padding: "12px 16px",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    fontSize: "0.8125rem",
                    width: col.width,
                    textAlign: col.align || "left",
                    cursor: col.sortable ? "pointer" : "default",
                    userSelect: "none",
                  }}
                  onClick={() => col.sortable && onSort && onSort(col.key)}
                >
                  <div
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      justifyContent: col.align === "right" ? "flex-end" : col.align === "center" ? "center" : "flex-start",
                    }}
                  >
                    <span>{col.header}</span>
                    {col.sortable && (
                      <span className="shrink-0 text-[var(--text-tertiary)]">
                        {isSorted ? (
                          sortDirection === "asc" ? <ArrowUp size={14} /> : <ArrowDown size={14} />
                        ) : (
                          <ArrowUpDown size={14} />
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
            <tr>
              <td colSpan={columns.length} style={{ padding: "32px", textAlign: "center" }}>
                <span style={{ color: "var(--text-secondary)" }}>Loading records...</span>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{ padding: "32px", textAlign: "center", color: "var(--text-tertiary)" }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={keyExtractor(row)}
                style={{
                  borderBottom: "1px solid var(--line-subtle)",
                  transition: "background-color var(--transition-fast)",
                }}
                className="hover:bg-[var(--brand-50)]"
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    style={{
                      padding: "14px 16px",
                      color: "var(--text-primary)",
                      textAlign: col.align || "left",
                    }}
                  >
                    {col.render ? col.render(row) : (row as any)[col.key]}
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

