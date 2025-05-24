'use client';

import React from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Check, ChevronDown, ZapIcon } from 'lucide-react';
import { ModelOption } from './_use-model-selection';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  modelOptions: ModelOption[];
  canAccessModel: (model: string) => boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  onModelChange,
  modelOptions,
}) => {
  const selectedLabel =
    modelOptions.find((o) => o.id === selectedModel)?.label || 'Select model';

  const handleSelect = (id: string) => {
    onModelChange(id);
  };

  return (
    <div className="relative">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="default"
            className="h-8 rounded-md text-muted-foreground shadow-none border-none focus:ring-0 px-3"
          >
            <div className="flex items-center gap-1 text-sm font-medium">
              <span>{selectedLabel}</span>
              <ChevronDown className="h-3 w-3 opacity-50 ml-1" />
            </div>
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-64 p-1">
          {modelOptions.map((opt) => (
            <DropdownMenuItem
              key={opt.id}
              className="text-sm py-3 px-3 flex items-start cursor-pointer rounded-md"
              onClick={() => handleSelect(opt.id)}
            >
              <div className="flex flex-col w-full">
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    {opt.id === 'sonnet-3.7' && (
                      <ZapIcon className="h-4 w-4 text-yellow-500" />
                    )}
                    <span className="font-medium">{opt.label}</span>
                  </div>
                  {selectedModel === opt.id && (
                    <Check className="h-4 w-4 text-blue-500" />
                  )}
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {opt.description}
                </div>
              </div>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};