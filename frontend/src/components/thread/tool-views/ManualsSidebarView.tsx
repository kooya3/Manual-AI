import React from 'react';
import {
  Book,
  ChevronDown,
  ChevronRight,
  FileText,
  FolderTree,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Manual {
  name: string;
  path: string;
  full_path: string;
  size: number;
  modified: number;
  category: string;
}

interface ManualCategory {
  name: string;
  manuals: Manual[];
  subcategories: { [key: string]: ManualCategory };
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  let i = Math.floor(Math.log(bytes) / Math.log(k));
  
  // Cap at GB
  i = Math.min(i, sizes.length - 1);
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function organizeManualsByCategory(manuals: Manual[]): ManualCategory {
  const root: ManualCategory = { name: 'root', manuals: [], subcategories: {} };

  manuals.forEach(manual => {
    const categories = manual.category.split(' > ').filter(Boolean);
    let currentLevel = root;

    categories.forEach(category => {
      if (!currentLevel.subcategories[category]) {
        currentLevel.subcategories[category] = {
          name: category,
          manuals: [],
          subcategories: {}
        };
      }
      currentLevel = currentLevel.subcategories[category];
    });

    currentLevel.manuals.push(manual);
  });

  return root;
}

const CategoryNode: React.FC<{
  category: ManualCategory;
  level?: number;
  onSelectManual: (manual: Manual) => void;
}> = ({ category, level = 0, onSelectManual }) => {
  const [isExpanded, setIsExpanded] = React.useState(true);
  const hasContent = category.manuals.length > 0 || Object.keys(category.subcategories).length > 0;

  if (!hasContent) return null;

  return (
    <div className="flex flex-col">
      {category.name !== 'root' && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            'flex items-center gap-1 p-1 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800',
            'text-sm font-medium text-zinc-700 dark:text-zinc-300',
          )}
          style={{ marginLeft: `${level * 12}px` }}
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <FolderTree className="h-4 w-4 mr-1 text-zinc-500" />
          {category.name}
        </button>
      )}

      {isExpanded && (
        <>
          {/* Show manuals in this category */}
          {category.manuals.map((manual, idx) => (
            <button
              key={`${manual.full_path}-${idx}`}
              onClick={() => onSelectManual(manual)}
              className={cn(
                'flex items-center gap-2 p-1 rounded text-left',
                'hover:bg-zinc-100 dark:hover:bg-zinc-800',
                'text-sm text-zinc-600 dark:text-zinc-400',
              )}
              style={{ marginLeft: `${(level + 1) * 12}px` }}
            >
              <FileText className="h-4 w-4 flex-shrink-0" />
              <span className="truncate">{manual.name}</span>
            </button>
          ))}

          {/* Render subcategories */}
          {Object.values(category.subcategories).map((subcategory, idx) => (
            <CategoryNode
              key={`${subcategory.name}-${idx}`}
              category={subcategory}
              level={level + 1}
              onSelectManual={onSelectManual}
            />
          ))}
        </>
      )}
    </div>
  );
};

interface ManualsSidebarProps {
  manuals: Manual[];
  onSelectManual: (manual: Manual) => void;
}

export function ManualsSidebarView({ manuals, onSelectManual }: ManualsSidebarProps) {
  const categorizedManuals = React.useMemo(() => {
    return organizeManualsByCategory(manuals);
  }, [manuals]);

  return (
    <div className="w-64 border-r border-zinc-200 dark:border-zinc-800 h-full flex flex-col">
      <div className="flex items-center p-2 border-b border-zinc-200 dark:border-zinc-800">
        <Book className="h-4 w-4 mr-2 text-zinc-600 dark:text-zinc-400" />
        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Product Manuals
        </span>
      </div>
      
      <div className="flex-1 overflow-auto p-2">
        <CategoryNode
          category={categorizedManuals}
          onSelectManual={onSelectManual}
        />
      </div>
    </div>
  );
}
