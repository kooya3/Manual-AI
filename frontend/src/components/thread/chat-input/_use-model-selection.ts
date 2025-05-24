'use client';

import { useState, useEffect } from 'react';

export const STORAGE_KEY_MODEL = 'suna-preferred-model';
export const DEFAULT_MODEL_ID = 'sonnet-3.7';

export interface ModelOption {
  id: string;
  label: string;
  description?: string;
}

export const MODEL_OPTIONS: ModelOption[] = [
  { 
    id: 'sonnet-3.7', 
    label: 'Standard', 
    description: 'Excellent for complex tasks and nuanced conversations'
  },
];

export const useModelSelection = () => {
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL_ID);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    try {
      const savedModel = localStorage.getItem(STORAGE_KEY_MODEL);
      if (savedModel && MODEL_OPTIONS.find(option => option.id === savedModel)) {
        setSelectedModel(savedModel);
      } else {
        localStorage.setItem(STORAGE_KEY_MODEL, DEFAULT_MODEL_ID);
      }
    } catch (error) {
      console.warn('Failed to load/save preferences from localStorage:', error);
    }
  }, []);

  const handleModelChange = (modelId: string) => {
    const modelOption = MODEL_OPTIONS.find(option => option.id === modelId);
    if (!modelOption) return;
    
    setSelectedModel(modelId);
    try {
      localStorage.setItem(STORAGE_KEY_MODEL, modelId);
    } catch (error) {
      console.warn('Failed to save model preference to localStorage:', error);
    }
  };

  return {
    selectedModel,
    setSelectedModel: handleModelChange,
    availableModels: MODEL_OPTIONS,
    allModels: MODEL_OPTIONS,
    canAccessModel: () => true,
    isSubscriptionRequired: () => false
  };
};