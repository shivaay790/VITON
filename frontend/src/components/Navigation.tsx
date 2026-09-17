import { ShoppingBag, Shirt, Palette, Gamepad2, ShoppingCart } from 'lucide-react';
import { useCart } from '../context/CartContext';

interface NavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = [
  { id: 'shop', label: 'Shop', icon: ShoppingBag },
  { id: 'tryon', label: 'Try-On', icon: Shirt },
  { id: 'designer', label: 'Designer', icon: Palette },
  { id: 'game', label: 'Style Game', icon: Gamepad2 },

  { id: 'cart', label: 'Cart', icon: ShoppingCart }
];

export function Navigation({ activeTab, onTabChange }: NavigationProps) {
  const { getTotalItems } = useCart();
  const cartItems = getTotalItems();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight flex items-center">
              <span className="bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">Top</span>
              <span className="text-gray-900">Trends</span>
              <div className="ml-2 w-2 h-2 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full animate-pulse"></div>
            </h1>
          </div>
          
          <div className="flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`relative px-4 py-2 rounded-lg transition-all duration-200 flex items-center space-x-2 ${
                    isActive
                      ? 'bg-pink-50 text-pink-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon size={18} />
                  <span className="hidden sm:inline font-medium">{tab.label}</span>
                  {tab.id === 'cart' && cartItems > 0 && (
                    <span className="absolute -top-2 -right-2 bg-pink-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {cartItems}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}