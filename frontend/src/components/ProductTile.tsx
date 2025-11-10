import React, { useState } from 'react';
import { Heart, ShoppingCart } from 'lucide-react';
import { Product } from '../types';
import { useCart } from '../context/CartContext';

interface ProductTileProps {
  product: Product;
  onTryOn?: (product: Product) => void;
}

export function ProductTile({ product, onTryOn }: ProductTileProps) {
  const [selectedSize, setSelectedSize] = useState(
    product.size && product.size.length > 0 ? product.size[0] : 'M'
  );
  const [isLiked, setIsLiked] = useState(false);
  const [showSizes, setShowSizes] = useState(false);
  const { addToCart } = useCart();

  const handleAddToCart = () => {
    addToCart(product, selectedSize);
    // Show a brief success animation
    const button = document.getElementById(`cart-btn-${product.id}`);
    if (button) {
      button.classList.add('animate-pulse');
      setTimeout(() => button.classList.remove('animate-pulse'), 600);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden group">
      <div className="relative aspect-[3/4] overflow-hidden">
        <img
          src={product.image}
          alt={product.title}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
        />
        
        {/* Brand Badge */}
        <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm px-2 py-1 rounded-lg">
          <span className="text-xs font-semibold text-gray-800">{product.company}</span>
        </div>
        
        <button
          onClick={() => setIsLiked(!isLiked)}
          className="absolute top-3 right-3 p-2 bg-white/80 backdrop-blur-sm rounded-full hover:bg-white hover:scale-110 transition-all duration-200"
        >
          <Heart
            size={18}
            className={`transition-colors ${
              isLiked ? 'fill-pink-500 text-pink-500' : 'text-gray-600'
            }`}
          />
        </button>
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        
        <div className="absolute bottom-3 left-3 right-3 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-2 group-hover:translate-y-0">
          <div className="flex space-x-2">
            {onTryOn && (
              <button
                onClick={() => onTryOn(product)}
                className="flex-1 bg-white/95 backdrop-blur-sm text-gray-900 py-2 px-4 rounded-lg font-medium hover:bg-white hover:shadow-lg transition-all duration-200"
              >
                Try On
              </button>
            )}
            <button
              onClick={() => setShowSizes(!showSizes)}
              className="flex-1 bg-gradient-to-r from-pink-500 to-purple-500 text-white py-2 px-4 rounded-lg font-medium hover:from-pink-600 hover:to-purple-600 hover:shadow-lg transition-all duration-200"
            >
              Quick Add
            </button>
          </div>
        </div>
      </div>

      {showSizes && (
        <div className="p-3 bg-gray-50 border-t">
          <div className="flex flex-wrap gap-2 mb-3">
            {(product.size && product.size.length > 0 ? product.size : ['M']).map((size) => (
              <button
                key={size}
                onClick={() => setSelectedSize(size)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  selectedSize === size
                    ? 'bg-pink-500 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
          <button
            id={`cart-btn-${product.id}`}
            onClick={handleAddToCart}
            className="w-full bg-gray-900 text-white py-2 rounded-lg font-medium hover:bg-gray-800 transition-colors flex items-center justify-center space-x-2"
          >
            <ShoppingCart size={16} />
            <span>Add to Cart</span>
          </button>
        </div>
      )}

      <div className="p-4">
        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">{product.title}</h3>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-gray-500">{product.company}</p>
          <div className="flex items-center space-x-1">
            <div className={`w-3 h-3 rounded-full border-2 border-gray-200`} style={{ backgroundColor: product.color }} />
            <span className="text-xs text-gray-400 capitalize">{product.color}</span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <p className="text-lg font-bold text-gray-900">${product.price}</p>
          <div className="flex items-center space-x-1">
            <span className="text-yellow-400">★</span>
            <span className="text-sm text-gray-500">4.{Math.floor(Math.random() * 9) + 1}</span>
          </div>
        </div>
      </div>
    </div>
  );
}