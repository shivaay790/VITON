import { useState, useEffect } from 'react';
import { Search, SlidersHorizontal, Sparkles } from 'lucide-react';
import { Product } from '../types';
import { api } from '../utils/api';
import { ProductTile } from './ProductTile';
import { FilterSidebar } from './FilterSidebar';

interface ShopProps {
  onTryOn: (product: Product) => void;
}

export function Shop({ onTryOn, products, setProducts }: ShopProps & { products: Product[], setProducts: (products: Product[]) => void }) {
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  // Separate pendingFilters for sidebar UI, and filters for applied filters
  const [pendingFilters, setPendingFilters] = useState({
    category: '',
    color: '',
    company: '',
    priceMax: 2000
  });
  const [, setFilters] = useState({
    category: '',
    color: '',
    company: '',
    priceMax: 2000
  });

  // Handle filter sidebar changes (update pendingFilters only)
  const handlePendingFilterChange = (key: string, value: string | number) => {
    setPendingFilters(prev => ({ ...prev, [key]: value }));
  };

  // Modified handleApplyFilters to also clear search
  const handleApplyFilters = async () => {
    setFilters({ ...pendingFilters });
    setSearchQuery(''); // Clear search when filters are applied
    try {
      const results = await api.searchClothes({
        category: pendingFilters.category,
        company: pendingFilters.company,
        color: pendingFilters.color,
        priceMax: pendingFilters.priceMax
      });
      setProducts(results);
    } catch (error) {
      console.error('Filter error:', error);
    }
  };

  // Helper to fetch all products (as on initial load)
  const fetchAllProducts = async () => {
    try {
      const results = await api.searchClothes({});
      setProducts(results);
    } catch (error) {
      console.error('Fetch all products error:', error);
    }
  };

  // Modified handleClearFilters to reset everything and fetch all products
  const handleClearFilters = async () => {
    setPendingFilters({ category: '', color: '', company: '', priceMax: 2000 });
    setFilters({ category: '', color: '', company: '', priceMax: 2000 });
    setSearchQuery('');
    await fetchAllProducts();
  };

  // Modified handleClearSearch to reset everything and fetch all products
  const handleClearSearch = async () => {
    setSearchQuery('');
    setPendingFilters({ category: '', color: '', company: '', priceMax: 2000 });
    setFilters({ category: '', color: '', company: '', priceMax: 2000 });
    await fetchAllProducts();
  };

  // Modified handleSearch to clear filters, then search
  const handleSearch = async (inputQuery?: string) => {
    const queryToUse = inputQuery !== undefined ? inputQuery : searchQuery;
    setSearchQuery(queryToUse);
    setPendingFilters({ category: '', color: '', company: '', priceMax: 2000 });
    setFilters({ category: '', color: '', company: '', priceMax: 2000 });
    try {
      const results = await api.searchClothes({ query: queryToUse });
      setProducts(results);
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  // On initial load, fetch all products
  useEffect(() => {
    fetchAllProducts();
    // eslint-disable-next-line
  }, []);

  const handleGetRecommendations = async () => {
    setIsLoadingRecommendations(true);
    try {
      const recs = await api.recommend();
      setRecommendations(recs);
    } catch (error) {
      console.error('Recommendation error:', error);
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  return (
    <div className="flex bg-gray-50 min-h-screen">
      <FilterSidebar
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        filters={pendingFilters}
        onFilterChange={handlePendingFilterChange}
        onClearFilters={handleClearFilters}
        onApplyFilters={handleApplyFilters}
      />

      <div className="flex-1 lg:ml-80">
        <div className="p-6">
          {/* Search and Filter Header */}
          <div className="flex items-center space-x-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search for items..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                onKeyDown={e => { if (e.key === 'Enter') handleSearch(e.currentTarget.value); }}
              />
            </div>
            <button
              onClick={() => handleSearch(searchQuery)}
              className="bg-pink-500 text-white px-4 py-2 rounded-xl font-medium hover:bg-pink-600 transition-colors"
            >
              Search
            </button>
            <button
              onClick={handleClearSearch}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded-xl font-medium hover:bg-gray-300 transition-colors"
            >
              Clear Search
            </button>
            <button
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className="lg:hidden bg-white p-3 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <SlidersHorizontal size={20} />
            </button>
          </div>

          {/* AI Recommendations Section */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">AI Recommendations</h2>
              <button
                onClick={handleGetRecommendations}
                disabled={isLoadingRecommendations}
                className="bg-gradient-to-r from-pink-500 to-purple-500 text-white px-6 py-2 rounded-xl font-medium hover:from-pink-600 hover:to-purple-600 transition-all flex items-center space-x-2 disabled:opacity-50"
              >
                <Sparkles size={16} />
                <span>{isLoadingRecommendations ? 'Loading...' : 'Recommend Me'}</span>
              </button>
            </div>
            {recommendations.length > 0 && (
              <div className="overflow-x-auto pb-4">
                <div className="flex space-x-4 w-max">
                  {recommendations.map((product) => (
                    <div key={product.id} className="w-64 flex-shrink-0">
                      <ProductTile product={product} onTryOn={onTryOn} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Main Product Grid */}
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Premium Tops Collection ({products.length})
            </h2>
            {products.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No tops found matching your criteria.</p>
                <button
                  onClick={handleClearFilters}
                  className="mt-4 text-pink-500 hover:text-pink-600 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {products.map((product) => (
                  <ProductTile key={product.id} product={product} onTryOn={onTryOn} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
