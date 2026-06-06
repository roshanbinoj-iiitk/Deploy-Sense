import Link from 'next/link';

interface FilterBarProps {
  items: { label: string; href: string }[];
  activeValue?: string | null;
  basePath: string;
}

export default function FilterBar({ items, activeValue, basePath }: FilterBarProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <Link
        href={basePath}
        className={`ds-filter-chip ${!activeValue ? 'active' : ''}`}
      >
        All
      </Link>
      {items.map(({ label, href }) => (
        <Link
          key={label}
          href={href}
          className={`ds-filter-chip ${activeValue === label ? 'active' : ''}`}
        >
          {label.replace('_', ' ')}
        </Link>
      ))}
    </div>
  );
}
