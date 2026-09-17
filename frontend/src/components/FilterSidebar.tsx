import { Filter, X } from 'lucide-react';
import { categories, companies, colors } from '../data/constants';

interface FilterSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  filters: {
    category: string;
    color: string;
    company: string;
    priceMax: number;
  };
  onFilterChange: (key: string, value: string | number) => void;
  onClearFilters: () => void;
  onApplyFilters: () => void;
}

export function FilterSidebar({ isOpen, onClose, filters, onFilterChange, onClearFilters, onApplyFilters }: FilterSidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed lg:sticky top-16 left-0 h-[calc(100vh-4rem)] w-80 bg-white z-50 transform transition-transform duration-300 overflow-y-auto
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Filter className="mr-2" size={20} />
              Filters
            </h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={onClose}
                className="lg:hidden p-1 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>
          </div>
          {/* Apply/Clear Filters at the top */}
          <div className="flex space-x-2 mb-6">
            <button
              onClick={onApplyFilters}
              className="flex-1 bg-pink-500 text-white py-2 rounded-lg font-medium hover:bg-pink-600 transition-colors"
            >
              Apply Filters
            </button>
            <button
              onClick={onClearFilters}
              className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Clear Filters
            </button>
          </div>
          <div className="space-y-6">
            {/* Category Filter */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Category</h3>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="category"
                    value=""
                    checked={filters.category === ''}
                    onChange={(e) => onFilterChange('category', e.target.value)}
                    className="text-pink-500 focus:ring-pink-500"
                  />
                  <span className="ml-2 text-gray-700">All Tops</span>
                </label>
                {categories.map((category) => (
                  <label key={category.value} className="flex items-center">
                    <input
                      type="radio"
                      name="category"
                      value={category.value}
                      checked={filters.category === category.value}
                      onChange={(e) => onFilterChange('category', e.target.value)}
                      className="text-pink-500 focus:ring-pink-500"
                    />
                    <span className="ml-2 text-gray-700">{category.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Company Filter */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Brand</h3>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="company"
                    value=""
                    checked={filters.company === ''}
                    onChange={(e) => onFilterChange('company', e.target.value)}
                    className="text-pink-500 focus:ring-pink-500"
                  />
                  <span className="ml-2 text-gray-700">All Brands</span>
                </label>
                {companies.map((company) => (
                  <label key={company} className="flex items-center">
                    <input
                      type="radio"
                      name="company"
                      value={company}
                      checked={filters.company === company}
                      onChange={(e) => onFilterChange('company', e.target.value)}
                      className="text-pink-500 focus:ring-pink-500"
                    />
                    <span className="ml-2 text-gray-700">{company}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Color Filter */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Color</h3>
              <div className="grid grid-cols-3 gap-2">
                {colors.map((color) => (
                  <button
                    key={color}
                    onClick={() => onFilterChange('color', filters.color === color ? '' : color)}
                    className={`h-8 rounded-lg border-2 transition-all ${
                      filters.color === color
                        ? 'border-pink-500 scale-110'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    style={{
                      backgroundColor: color === 'floral' ? '#fce7f3' : color
                    }}
                    title={color}
                  />
                ))}
              </div>
            </div>

            {/* Price Filter */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Max Price</h3>
              <input
                type="range"
                min="0"
                max="2000"
                value={filters.priceMax}
                onChange={(e) => onFilterChange('priceMax', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>$0</span>
                <span>${filters.priceMax}</span>
                <span>$2000</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}