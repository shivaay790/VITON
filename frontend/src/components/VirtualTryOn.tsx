import React, { useState, useEffect } from 'react';
import { Upload, User, Shirt, Wand2, RefreshCw } from 'lucide-react';
import { api } from '../utils/api';
import { Product } from '../types';

interface VirtualTryOnProps {
  selectedProduct: Product | null;
}

export function VirtualTryOn({ selectedProduct }: VirtualTryOnProps) {
  const [humanImage, setHumanImage] = useState<File | null>(null);
  const [clothingImage, setClothingImage] = useState<File | null>(null);
  const [clothingImageUrl, setClothingImageUrl] = useState<string | null>(null);
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-set clothing image if selectedProduct is present
  useEffect(() => {
    async function fetchClothFile() {
      if (selectedProduct && selectedProduct.image) {
        // Fetch the image as a blob and create a File object
        const response = await fetch(selectedProduct.image);
        const blob = await response.blob();
        const file = new File([blob], selectedProduct.image.split('/').pop() || 'shop_cloth.jpg', { type: blob.type });
        setClothingImage(file);
        setClothingImageUrl(selectedProduct.image);
      }
    }
    if (selectedProduct) {
      fetchClothFile();
    }
  }, [selectedProduct]);

  const handleImageUpload = (type: 'human' | 'clothing', file: File) => {
    if (type === 'human') {
      setHumanImage(file);
    } else {
      setClothingImage(file);
      setClothingImageUrl(URL.createObjectURL(file));
    }
    setError(null);
  };

  const handleTryOn = async () => {
    if (!humanImage || (!clothingImage && !clothingImageUrl)) {
      setError('Please upload both a person image and a clothing image.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      // Use the API utility for consistent endpoint handling
      const resultUrl = await api.tryOn(humanImage, clothingImage || undefined);
      setResultImage(resultUrl);
    } catch (err) {
      console.error('Try-on error:', err);
      setError('Failed to generate try-on. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetTryOn = () => {
    setHumanImage(null);
    setClothingImage(null);
    setClothingImageUrl(null);
    setResultImage(null);
    setError(null);
  };

  const ImageUploadArea = ({ 
    type, 
    icon: Icon, 
    title, 
    file, 
    imageUrl, 
    onUpload 
  }: { 
    type: 'human' | 'clothing';
    icon: any;
    title: string;
    file: File | null;
    imageUrl?: string | null;
    onUpload: (file: File) => void;
  }) => (
    <div className="relative">
      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUpload(file);
        }}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
      />
      <div className={`
        border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300 hover:border-pink-400 hover:bg-pink-50/50
        ${file || imageUrl ? 'border-pink-500 bg-pink-50' : 'border-gray-300'}
      `}>
        {imageUrl ? (
          <img src={imageUrl} alt={title} className="mx-auto mb-4 max-h-40 object-contain" />
        ) : (
          <Icon className={`mx-auto mb-4 ${file ? 'text-pink-500' : 'text-gray-400'}`} size={48} />
        )}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        {file ? (
          <p className="text-sm text-pink-600 font-medium">{file.name}</p>
        ) : imageUrl ? (
          <p className="text-sm text-pink-600 font-medium">Selected from shop</p>
        ) : (
          <p className="text-sm text-gray-500">Click to upload or drag and drop</p>
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Virtual Try-On Studio</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Upload your photo and select from our premium tops collection to see how it looks on you with our AI-powered virtual try-on technology.
        </p>
      </div>

      {!resultImage ? (
        <div className="space-y-8">
          {/* Upload Areas */}
          <div className="grid md:grid-cols-2 gap-8">
            <ImageUploadArea
              type="human"
              icon={User}
              title="Upload Your Photo"
              file={humanImage}
              onUpload={(file) => handleImageUpload('human', file)}
            />
            <ImageUploadArea
              type="clothing"
              icon={Shirt}
              title="Selected Top"
              file={clothingImage}
              imageUrl={clothingImageUrl}
              onUpload={(file) => handleImageUpload('clothing', file)}
            />
          </div>
          {error && <div className="text-red-500 text-center">{error}</div>}
          <div className="flex justify-center space-x-4">
            <button
              onClick={handleTryOn}
              disabled={isLoading || !humanImage || !clothingImage}
              className="bg-pink-500 text-white px-8 py-3 rounded-xl font-semibold hover:bg-pink-600 transition-colors disabled:opacity-50 flex items-center space-x-2"
            >
              {isLoading ? <RefreshCw className="animate-spin" size={20} /> : <Wand2 size={20} />}
              <span>Generate</span>
            </button>
            <button
              onClick={resetTryOn}
              className="bg-gray-200 text-gray-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-300 transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center">
          <img src={resultImage} alt="Try-On Result" className="mx-auto rounded-2xl shadow-lg max-h-[500px]" />
          <div className="flex justify-center mt-6 space-x-4">
            <button
              onClick={resetTryOn}
              className="bg-gray-200 text-gray-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-300 transition-colors"
            >
              Try Another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}