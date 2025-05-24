'use client';

import Image from 'next/image';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function KortixLogo() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // After mount, we can access the theme
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="flex h-12 w-12 items-center justify-center flex-shrink-0">
      <Image
      src="/kortix-symbol.svg"
      alt="Manual Agent"
      width={68}
      height={68}
      className={`${mounted && theme === 'dark' ? 'invert' : 'to-blue-600'}`}
      />
    </div>
  );
}
