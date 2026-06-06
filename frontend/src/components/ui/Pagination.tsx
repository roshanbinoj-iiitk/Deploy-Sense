import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  page: number;
  totalPages: number;
  buildUrl: (page: number) => string;
}

export default function Pagination({ page, totalPages, buildUrl }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages = Array.from(
    { length: Math.min(7, totalPages) },
    (_, i) => Math.max(1, Math.min(totalPages - 6, page - 3)) + i,
  );

  return (
    <div className="flex items-center justify-center gap-1.5">
      {page > 1 && (
        <Link href={buildUrl(page - 1)} className="ds-page-btn flex items-center gap-1">
          <ChevronLeft className="h-3.5 w-3.5" />
          Prev
        </Link>
      )}
      {pages.map(p => (
        <Link
          key={p}
          href={buildUrl(p)}
          className={`ds-page-btn ${p === page ? 'active' : ''}`}
        >
          {p}
        </Link>
      ))}
      {page < totalPages && (
        <Link href={buildUrl(page + 1)} className="ds-page-btn flex items-center gap-1">
          Next
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      )}
    </div>
  );
}
