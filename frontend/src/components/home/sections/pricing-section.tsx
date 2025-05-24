'use client';

import { SectionHeader } from '@/components/home/section-header';
import { motion } from 'motion/react';
import { CheckIcon } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

// Constants
const FREE_PLAN_FEATURES = [
  'Upload and manage manuals',
  'AI-powered product search',
  'Voice interface',
  'Real-time product data',
  'Analytics dashboard',
];

// Components
export function PricingSection() {
  return (
    <section
      id="pricing"
      className="container py-8 md:py-12 lg:py-24"
      aria-label="Pricing"
    >
      
      <div className="grid gap-8 mt-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative rounded-2xl border bg-background p-6 shadow-lg"
        >
          <div className="flex flex-col gap-8">
            <div>
              <h3 className="text-2xl font-bold">Free Plan</h3>
              <p className="mt-2 text-muted-foreground">
                All features included at no cost
              </p>
            </div>
            <div className="space-y-4">
              {FREE_PLAN_FEATURES.map((feature) => (
                <div key={feature} className="flex items-center gap-2">
                  <CheckIcon className="h-4 w-4 text-green-500" />
                  <span>{feature}</span>
                </div>
              ))}
            </div>
            <div>
              <Button asChild className="w-full">
                <Link href="/chat">Get Started</Link>
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
