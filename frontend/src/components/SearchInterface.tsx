import React, { useState, useCallback, useEffect } from 'react';
import type { SearchResult, SearchResponse } from '../services/api';
import { apiService } from '../services/api';
import SearchResultCard from './SearchResultCard';
import LoadingSpinner from './LoadingSpinner';

interface SearchInterfaceProps {
  onDocumentSelect?: (documentId: string) => void;
}

// Simple debounce function
function debounce<T extends (...args: any[]) => any>(func: T, delay: number): T {
  let timeoutId: number;
  return ((...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => func(...args), delay);
  }) as T;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({ onDocumentSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recent_searches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // Save search to recent searches
  const saveSearch = (searchQuery: string) => {
    const updated = [searchQuery, ...recentSearches.filter(s => s !== searchQuery)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recent_searches', JSON.stringify(updated));
  };

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        setHasSearched(false);
        return;
      }

      setIsLoading(true);
      try {
        const response: SearchResponse = await apiService.searchDocuments(searchQuery, 10);
        setResults(response.results);
        setHasSearched(true);
        saveSearch(searchQuery);
      } catch (error) {
        console.error('Search error:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    [recentSearches]
  );

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setShowSuggestions(value.length === 0);
    debouncedSearch(value);
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    debouncedSearch(suggestion);
  };

  // Clear search
  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setHasSearched(false);
    setShowSuggestions(false);
  };

  // Sample suggestions for empty state
  const sampleQueries = [
    "Employee handbook policies",
    "Vacation request forms",
    "IT security protocols",
    "Budget planning templates",
    "Performance review guidelines"
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <span className="text-2xl mr-3">✨</span>
          <h1 className="text-3xl font-bold text-gray-900">AI Document Search</h1>
        </div>
        <p className="text-gray-600">
          Ask questions or search for documents using natural language
        </p>
      </div>

      {/* Search Input */}
      <div className="relative mb-6">
        <div className="relative">
          <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={() => setShowSuggestions(query.length === 0)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="Ask anything about your documents..."
            className="w-full pl-12 pr-12 py-4 text-lg border-2 border-gray-200 rounded-2xl focus:border-primary-500 focus:ring-0 transition-colors duration-200"
          />
          {query && (
            <button
              onClick={clearSearch}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>

        {/* Search Suggestions */}
        {showSuggestions && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-lg border border-gray-200 z-50">
            <div className="p-4">
              {recentSearches.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <span className="mr-1">🕒</span>
                    Recent Searches
                  </h3>
                  {recentSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(search)}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                    >
                      {search}
                    </button>
                  ))}
                </div>
              )}
              
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Try asking:</h3>
                {sampleQueries.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
          <span className="ml-3 text-gray-600">Searching documents...</span>
        </div>
      )}

      {/* Search Results */}
      {!isLoading && hasSearched && (
        <div>
          {results.length > 0 ? (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Found {results.length} relevant document{results.length !== 1 ? 's' : ''}
                </h2>
                <span className="text-sm text-gray-500">
                  for "{query}"
                </span>
              </div>

              <div className="space-y-4">
                {results.map((result) => (
                  <SearchResultCard
                    key={result.document.id}
                    result={result}
                    onSelect={onDocumentSelect}
                    searchQuery={query}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <span className="text-6xl text-gray-300 mb-4 block">📄</span>
              <h3 className="text-lg font-medium text-gray-700 mb-2">No documents found</h3>
              <p className="text-gray-500">
                Try rephrasing your question or using different keywords
              </p>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !hasSearched && query.length === 0 && (
        <div className="text-center py-12">
          <span className="text-6xl text-primary-300 mb-4 block">✨</span>
          <h3 className="text-lg font-medium text-gray-700 mb-2">AI-Powered Document Search</h3>
          <p className="text-gray-500 mb-6">
            Search through your documents using natural language queries
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {sampleQueries.slice(0, 3).map((query, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(query)}
                className="px-4 py-2 bg-primary-50 text-primary-700 rounded-full text-sm hover:bg-primary-100 transition-colors duration-200"
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchInterface; 