import { useState, useEffect } from 'react';
import { CartProvider } from './context/CartContext';
import { Navigation } from './components/Navigation';
import { Chatbot } from './components/Chatbot';
import { Shop } from './components/Shop';
import { VirtualTryOn } from './components/VirtualTryOn';
import { DesignerStudio } from './components/DesignerStudio';
import { StyleGame } from './components/StyleGame';

import { Cart } from './components/Cart';
import { Product } from './types';
import { api } from './utils/api';
import { filenameToProduct } from './utils/productMetadata';

function App() {
  const [activeTab, setActiveTab] = useState('shop');
  const [selectedTryOnProduct, setSelectedTryOnProduct] = useState<Product | null>(null);
  const [backendStatus, setBackendStatus] = useState<string>('');
  const [products, setProducts] = useState<Product[]>([]);

  const handleTryOn = (product: Product) => {
    setSelectedTryOnProduct(product);
    setActiveTab('tryon');
  };

  // Listen for custom tab change events
  useEffect(() => {
    const handleTabChange = (event: Event) => {
      setActiveTab((event as CustomEvent<string>).detail);
    };

    window.addEventListener('changeTab', handleTabChange);
    return () => window.removeEventListener('changeTab', handleTabChange);
  }, []);

  useEffect(() => {
    api.ping()
      .then(res => setBackendStatus(res.message))
      .catch(() => setBackendStatus('Backend not reachable'));
  }, []);

  useEffect(() => {
    api.getTops()
      .then(filenames => setProducts(filenames.map(filenameToProduct)))
      .catch(console.error);
  }, []);

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'shop':
        return <Shop onTryOn={handleTryOn} products={products} setProducts={setProducts} />;
      case 'tryon':
        return <VirtualTryOn selectedProduct={selectedTryOnProduct} />;
      case 'designer':
        return <DesignerStudio />;
      case 'game':
        return <StyleGame />;

      case 'cart':
        return <Cart />;
      default:
        return <Shop onTryOn={handleTryOn} products={products} setProducts={setProducts} />;
    }
  };

  return (
    <CartProvider>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-blue-100 text-blue-800 px-4 py-2 text-sm">Backend status: {backendStatus}</div>
        <div className="bg-amber-100 text-amber-900 px-4 py-2 text-sm font-medium border-b border-amber-200">
          Demonstration only: this is not an actual clothing e-commerce site. It is for an ML project demo.
        </div>
        <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="pb-8">
          {renderActiveTab()}
        </main>
        <Chatbot />
      </div>
    </CartProvider>
  );
}

export default App;