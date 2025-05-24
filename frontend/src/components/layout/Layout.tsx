import React from 'react';
import { ManualsSidebarView } from '../thread/tool-views/ManualsSidebarView';
import { useManualsStore } from '@/store/manualsStore';
import { motion, AnimatePresence } from 'framer-motion';

export function Layout({ children }: { children: React.ReactNode }) {
  const { isVisible, manuals, setSelectedManual } = useManualsStore();

  return (
    <div className="flex h-screen">
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ x: -256, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -256, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="h-full"
          >
            <ManualsSidebarView
              manuals={manuals}
              onSelectManual={setSelectedManual}
            />
          </motion.div>
        )}
      </AnimatePresence>
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
