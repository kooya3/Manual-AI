import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  Check, 
  AlertTriangle, 
  CircleDashed, 
  AlertCircle,
  ChevronDown,
  Search,
  X,
  Eye
} from 'lucide-react';
import { ToolViewProps } from './types';
import { formatTimestamp, getToolTitle } from './utils';
import { cn } from '@/lib/utils';
import { useManualsStore } from '@/store/manualsStore';
import { 
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent 
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

interface ManualInfo {
  name: string;
  path: string;
  full_path: string;
  size: number;
  modified: number;
  category: string;
  match_count?: number;
  categoryParts?: string[];
}

interface ManualContent {
  full_text: string;
  file_path: string;
  page_range: string;
  pdf_url?: string;
  extracted_text?: string;
  metadata?: {
    name: string;
    path: string;
    category: string;
    size: number;
    modified: number;
    pdf_url?: string;
  };
  matches?: Array<{
    text: string;
    match_position: [number, number];
    page: number;
    context: string;
    start: number;
    end: number;
  }>;
  match_count?: number;
}

interface ManualCategory {
  name: string;
  manuals: ManualInfo[];
  subcategories: { [key: string]: ManualCategory };
}

function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDate(timestamp: number) {
  return new Date(timestamp * 1000).toLocaleString();
}

/**
 * Extracts and parses the JSON content from the tool's assistantContent and toolContent
 */
function parseManualToolContent(assistantContent: string, toolContent: string) {
  // Extract arguments from assistant content
  let manualName = '';
  let searchTerm = '';
  
  if (assistantContent) {
    // For extract_manual_content
    const manualNameMatch = assistantContent.match(/<manual_name>([^]*?)<\/manual_name>/);
    if (manualNameMatch) {
      manualName = manualNameMatch[1];
    }
    
    // For search term in find_product_manual
    const searchTermMatch = assistantContent.match(/<product_name>([^]*?)<\/product_name>/);
    if (searchTermMatch) {
      searchTerm = searchTermMatch[1];
    }
  }
  
  // Parse the tool result
  let parsedToolContent: any = {};
  
  if (toolContent) {
    try {
      parsedToolContent = JSON.parse(toolContent);
    } catch (error) {
      console.error('Error parsing manual tool content:', error);
    }
  }
  
  return {
    manualName,
    searchTerm,
    parsedContent: parsedToolContent,
  };
}

export function ManualsToolView({
  name = 'list_manuals',
  assistantContent,
  toolContent,
  assistantTimestamp,
  toolTimestamp,
  isSuccess = true,
  isStreaming = false,
}: ToolViewProps) {
  const toolTitle = getToolTitle(name);
  const { 
    setManuals, 
    setVisible, 
    setSelectedManual, 
    activeCategory, 
    setActiveCategory 
  } = useManualsStore();
  
  // State management
  const [activeTab, setActiveTab] = useState<'manuals' | 'content'>('manuals');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchPage, setSearchPage] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'text' | 'pdf'>('text');

  useEffect(() => {
    // When manuals data is received, update the store
    if (toolContent && isSuccess) {
      try {
        const { manuals } = parseManualToolContent('', toolContent).parsedContent;
        if (manuals) {
          // Process the manuals to organize them by category
          const processedManuals = manuals.map((manual: ManualInfo) => ({
            ...manual,
            categoryParts: manual.category ? manual.category.split('/').filter(Boolean) : ['Uncategorized']
          }));
          setManuals(processedManuals);
          setVisible(true);
        }
      } catch (e) {
        console.error('Failed to parse manuals:', e);
      }
    }
  }, [toolContent, isSuccess, setManuals, setVisible]);

  // Parse the content
  const { manualName, searchTerm, parsedContent } = parseManualToolContent(assistantContent || '', toolContent || '');

  // Determine which tool function was called
  const isListManuals = name === 'list_manuals';
  const isFindProductManual = name === 'find_product_manual';
  const isExtractManualContent = name === 'extract_manual_content';

  // Change to content tab if extracting manual content
  useEffect(() => {
    if (isExtractManualContent) {
      setActiveTab('content');
    }
  }, [isExtractManualContent, setActiveTab]);

  // Function to render manual list
  const renderManualList = (manuals: ManualInfo[]) => {
    if (!manuals || manuals.length === 0) {
      return (
        <div className="py-4 text-center text-zinc-500 dark:text-zinc-400">
          <AlertCircle className="h-5 w-5 mx-auto mb-2" />
          <p>No manuals found</p>
        </div>
      );
    }

    // Filter manuals by active category if one is selected
    const filteredManuals = activeCategory
      ? manuals.filter(manual => manual.category?.includes(activeCategory))
      : manuals;

    // Group manuals by category
    const manualsByCategory = filteredManuals.reduce((acc, manual) => {
      const category = manual.categoryParts?.[0] || 'Uncategorized';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(manual);
      return acc;
    }, {} as Record<string, ManualInfo[]>);

    return (
      <div className="space-y-4">
        {Object.entries(manualsByCategory).map(([category, categoryManuals]) => (
          <div key={category} className="space-y-2">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">{category}</h3>
            <div className="space-y-2">
              {categoryManuals.map((manual, index) => (
                <Collapsible key={`${category}-${index}`} className="border rounded-md">
                  <div className="flex items-center p-3">
                    <FileText className="h-5 w-5 text-primary mr-2 flex-shrink-0" />
                    <div className="flex-1 mr-2 truncate">
                      <div className="font-medium truncate">{manual.name}</div>
                      <div className="text-xs text-zinc-500 dark:text-zinc-400">
                        {formatBytes(manual.size)} • Modified: {formatDate(manual.modified)}
                      </div>
                    </div>
                    <CollapsibleTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-7 w-7">
                        <ChevronDown className="h-4 w-4" />
                      </Button>
                    </CollapsibleTrigger>
                  </div>
                  <CollapsibleContent>
                    <div className="px-3 pb-3 pt-0 border-t">
                      <div className="text-sm mt-2 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-zinc-500 dark:text-zinc-400">File size:</span>
                          <span>{formatBytes(manual.size)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-zinc-500 dark:text-zinc-400">Last modified:</span>
                          <span>{formatDate(manual.modified)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-zinc-500 dark:text-zinc-400">Category:</span>
                          <span>{manual.category}</span>
                        </div>
                        <div className="pt-2 flex gap-2">
                          <Button 
                            size="sm" 
                            className="w-full"
                            onClick={() => {
                              setSelectedManual(manual);
                              setActiveTab('content');
                            }}
                          >
                            View Content
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Function to render manual content
  const renderManualContent = (content: ManualContent) => {
    if (!content) {
      return (
        <div className="py-4 text-center text-zinc-500 dark:text-zinc-400">
          <AlertCircle className="h-5 w-5 mx-auto mb-2" />
          <p>No content available</p>
        </div>
      );
    }

    // Add view mode toggle if PDF URL is available
    const pdfUrl = content.pdf_url || content.metadata?.pdf_url;
    const textContent = content.extracted_text || content.full_text;

    return (
      <div className="space-y-4">
        {pdfUrl && (
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              {content.matches && content.matches.length > 0 && (
                <Badge variant="outline" className="bg-primary/10 text-primary">
                  {content.match_count} matches found
                </Badge>
              )}
            </div>
            <div className="flex rounded-md overflow-hidden border border-zinc-200 dark:border-zinc-700">
              <button
                onClick={() => setViewMode('text')}
                className={cn(
                  'flex items-center gap-1 text-xs px-2 py-1 transition-colors',
                  viewMode === 'text'
                    ? 'bg-zinc-800 text-zinc-100 dark:bg-zinc-700 dark:text-zinc-100'
                    : 'bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400 hover:bg-zinc-300 dark:hover:bg-zinc-700',
                )}
              >
                <FileText className="h-3 w-3" />
                <span>Text</span>
              </button>
              <button
                onClick={() => setViewMode('pdf')}
                className={cn(
                  'flex items-center gap-1 text-xs px-2 py-1 transition-colors',
                  viewMode === 'pdf'
                    ? 'bg-zinc-800 text-zinc-100 dark:bg-zinc-700 dark:text-zinc-100'
                    : 'bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400 hover:bg-zinc-300 dark:hover:bg-zinc-700',
                )}
              >
                <Eye className="h-3 w-3" />
                <span>PDF</span>
              </button>
            </div>
          </div>
        )}

        {viewMode === 'text' && (
          <>
            {content.matches && content.matches.length > 0 ? (
              <div className="space-y-4">
                {content.matches.map((match, index) => {
                  const beforeMatch = match.context.substring(0, match.start);
                  const matchedText = match.context.substring(match.start, match.end);
                  const afterMatch = match.context.substring(match.end);

                  return (
                    <div key={index} className="border rounded-md p-3 bg-muted/50">
                      <div className="text-sm whitespace-pre-wrap font-mono">
                        {beforeMatch}
                        <span className="bg-yellow-200 dark:bg-yellow-900">{matchedText}</span>
                        {afterMatch}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-sm whitespace-pre-wrap font-mono">
                {textContent}
              </div>
            )}
          </>
        )}

        {viewMode === 'pdf' && pdfUrl && (
          <div className="flex-1 bg-white overflow-hidden">
            <iframe
              src={pdfUrl}
              title="Manual PDF Preview"
              className="w-full h-full border-0"
              style={{ minHeight: '600px' }}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
            />
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 pb-8">
        <Tabs value={activeTab} onValueChange={(value: "manuals" | "content") => setActiveTab(value)} className="h-full flex flex-col">
          <div className="px-1">
            <TabsList className="w-full grid grid-cols-2">
              <TabsTrigger value="manuals">Manuals</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
            </TabsList>
          </div>
          
          <div className="mt-4 px-1">
            {activeTab === 'manuals' && (
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500 dark:text-zinc-400" />
                <Input
                  type="search"
                  placeholder="Search product manuals..."
                  className="pl-9 w-full"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      setIsSearching(true);
                      // In a real implementation, this would trigger a search
                      setTimeout(() => setIsSearching(false), 1000);
                    }
                  }}
                />
                {searchQuery && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1 h-7 w-7"
                    onClick={() => setSearchQuery('')}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}
          </div>
          
          <TabsContent value="manuals" className="flex-1 mt-4">
            <ScrollArea className="h-[calc(100vh-220px)]">
              {isListManuals && !isSuccess && (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="border rounded-md p-3">
                      <div className="flex items-center">
                        <Skeleton className="h-5 w-5 mr-2" />
                        <div className="flex-1">
                          <Skeleton className="h-5 w-32 mb-1" />
                          <Skeleton className="h-3 w-24" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {isListManuals && isSuccess && renderManualList(parsedContent.manuals || [])}
              
              {isFindProductManual && !isSuccess && (
                <div className="p-4 text-center">
                  <Skeleton className="h-6 w-32 mx-auto mb-2" />
                  <Skeleton className="h-4 w-48 mx-auto" />
                </div>
              )}
              
              {isFindProductManual && isSuccess && (
                <div>
                  <div className="mb-4">
                    <h3 className="font-medium text-sm mb-1">
                      Search Results for "{searchTerm || 'product'}"
                    </h3>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      {parsedContent.message}
                    </p>
                  </div>
                  {renderManualList(parsedContent.manuals || [])}
                </div>
              )}
              
              {isSearching && (
                <div className="space-y-2 mt-4">
                  <div className="flex items-center justify-center py-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary/50 animate-pulse" />
                      <div className="h-1.5 w-1.5 rounded-full bg-primary/50 animate-pulse delay-150" />
                      <div className="h-1.5 w-1.5 rounded-full bg-primary/50 animate-pulse delay-300" />
                    </div>
                  </div>
                </div>
              )}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="content" className="flex-1 mt-4">
            <ScrollArea className="h-[calc(100vh-220px)]">
              {(!isExtractManualContent || !isSuccess) && !searchPage && (
                <div className="py-8 text-center text-zinc-500 dark:text-zinc-400">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Select a manual to view its content</p>
                </div>
              )}
              
              {isExtractManualContent && isSuccess && (
                <div>
                  <div className="mb-4 flex justify-between items-center">
                    <h3 className="font-medium">
                      {manualName || 'Manual Content'}
                    </h3>
                  </div>
                  
                  {renderManualContent(parsedContent.content || {})}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
