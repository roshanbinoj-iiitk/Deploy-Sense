import { ReactNode } from 'react';

interface PanelProps {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export default function Panel({ title, actions, children }: PanelProps) {
  return (
    <div className="ds-panel">
      {title && (
        <div className="ds-panel-head">
          <h2 className="text-sm font-semibold text-white">{title}</h2>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
