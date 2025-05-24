import { create } from 'zustand';

interface ManualInfo {
  name: string;
  path: string;
  full_path: string;
  size: number;
  modified: number;
  category: string;
  categoryParts?: string[];
  match_count?: number;
}

interface ManualsStore {
  manuals: ManualInfo[];
  selectedManual: ManualInfo | null;
  isVisible: boolean;
  activeCategory: string | null;
  setManuals: (manuals: ManualInfo[]) => void;
  setSelectedManual: (manual: ManualInfo | null) => void;
  setVisible: (visible: boolean) => void;
  toggleVisibility: () => void;
  setActiveCategory: (category: string | null) => void;
}

export const useManualsStore = create<ManualsStore>((set) => ({
  manuals: [],
  selectedManual: null,
  isVisible: false,
  activeCategory: null,
  setManuals: (manuals) => set({ 
    manuals: manuals.map(manual => ({
      ...manual,
      categoryParts: manual.category ? manual.category.split(' > ') : ['Uncategorized']
    }))
  }),
  setSelectedManual: (manual) => set({ selectedManual: manual }),
  setVisible: (visible) => set({ isVisible: visible }),
  toggleVisibility: () => set((state) => ({ isVisible: !state.isVisible })),
  setActiveCategory: (category) => set({ activeCategory: category })
}));
