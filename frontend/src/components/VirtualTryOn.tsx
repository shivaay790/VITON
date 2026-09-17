import { useEffect, useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import { User, Shirt, Wand2, RefreshCw } from 'lucide-react';
import { api } from '../utils/api';
import { Product } from '../types';
import { API_BASE_URL } from '../config';

interface VirtualTryOnProps {
  selectedProduct: Product | null;
}

interface ImageUploadAreaProps {
  icon: LucideIcon;
  title: string;
  file: File | null;
  imageUrl: string | null;
  caption?: string;
  onUpload: (file: File) => void;
}

// Defined outside VirtualTryOn so it is not re-created, and remounted, on every render.
function ImageUploadArea({ icon: Icon, title, file, imageUrl, caption, onUpload }: ImageUploadAreaProps) {
  return (
    <div className="relative">
      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          const picked = e.target.files?.[0];
          if (picked) onUpload(picked);
          e.target.value = '';
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
        <p className={`text-sm ${file || imageUrl ? 'text-pink-600 font-medium' : 'text-gray-500'}`}>
          {caption ?? (file ? file.name : 'Click to upload or drag and drop')}
        </p>
      </div>
    </div>
  );
}

async function urlToFile(url: string, name: string): Promise<File> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load ${name}`);
  const blob = await response.blob();
  return new File([blob], name, { type: blob.type || 'image/jpeg' });
}

export function VirtualTryOn({ selectedProduct }: VirtualTryOnProps) {
  const [humanImage, setHumanImage] = useState<File | null>(null);
  const [humanImageUrl, setHumanImageUrl] = useState<string | null>(null);
  const [humanCaption, setHumanCaption] = useState<string | undefined>(undefined);
  const [clothingImage, setClothingImage] = useState<File | null>(null);
  const [clothingImageUrl, setClothingImageUrl] = useState<string | null>(null);
  // Filename of a shop garment. Sent to the backend so it uses the dataset's real garment mask.
  const [shopCloth, setShopCloth] = useState<string | null>(null);
  const [samplePeople, setSamplePeople] = useState<string[]>([]);
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedProduct?.image) return;
    const name = selectedProduct.id;
    urlToFile(selectedProduct.image, name)
      .then((file) => {
        setClothingImage(file);
        setClothingImageUrl(selectedProduct.image);
        setShopCloth(name);
      })
      .catch(() => setError('Could not load the selected top from the backend.'));
  }, [selectedProduct]);

  useEffect(() => {
    // A spread of catalogue models from the dataset, so try-on can be tested without a photo to hand.
    api.getTops({ session_id: 'people', page: 1, pageSize: 48 })
      .then((names) => setSamplePeople(names.filter((_, i) => i % 6 === 0).slice(0, 8)))
      .catch(() => setSamplePeople([]));
  }, []);

  const handleHumanUpload = (file: File) => {
    setHumanImage(file);
    setHumanImageUrl(URL.createObjectURL(file));
    setHumanCaption(undefined);
    setError(null);
  };

  const handleClothingUpload = (file: File) => {
    setClothingImage(file);
    setClothingImageUrl(URL.createObjectURL(file));
    setShopCloth(null);
    setError(null);
  };

  const handleSamplePerson = async (name: string) => {
    try {
      const url = `${API_BASE_URL}/people/${name}`;
      setHumanImage(await urlToFile(url, name));
      setHumanImageUrl(url);
      setHumanCaption(`Sample model ${name.replace(/\.[^/.]+$/, '')}`);
      setError(null);
    } catch {
      setError('Could not load that sample model from the backend.');
    }
  };

  const handleTryOn = async () => {
    if (!humanImage || !clothingImage) {
      setError('Please choose both a person photo and a top.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setResultImage(await api.tryOn(humanImage, clothingImage, shopCloth ?? undefined));
    } catch (err) {
      console.error('Try-on error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate try-on. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetTryOn = () => {
    setHumanImage(null);
    setHumanImageUrl(null);
    setHumanCaption(undefined);
    setClothingImage(null);
    setClothingImageUrl(null);
    setShopCloth(null);
    setResultImage(null);
    setError(null);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Virtual Try-On Studio</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Upload your photo, or pick a sample model, and choose a top from the shop to see it on you.
          Works best with a front-facing photo against a plain background.
        </p>
      </div>

      {!resultImage ? (
        <div className="space-y-8">
          <div className="grid md:grid-cols-2 gap-8">
            <ImageUploadArea
              icon={User}
              title="Your Photo"
              file={humanImage}
              imageUrl={humanImageUrl}
              caption={humanCaption}
              onUpload={handleHumanUpload}
            />
            <ImageUploadArea
              icon={Shirt}
              title="Selected Top"
              file={clothingImage}
              imageUrl={clothingImageUrl}
              caption={shopCloth ? 'Selected from shop' : undefined}
              onUpload={handleClothingUpload}
            />
          </div>

          {samplePeople.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-3">No photo to hand? Pick a sample model:</p>
              <div className="flex flex-wrap gap-3">
                {samplePeople.map((name) => (
                  <button
                    key={name}
                    onClick={() => handleSamplePerson(name)}
                    className={`w-16 h-20 rounded-lg overflow-hidden border-2 transition-colors ${
                      humanCaption?.endsWith(name.replace(/\.[^/.]+$/, '')) ? 'border-pink-500' : 'border-transparent hover:border-pink-300'
                    }`}
                    title={name}
                  >
                    <img src={`${API_BASE_URL}/people/${name}`} alt={name} className="w-full h-full object-cover" loading="lazy" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {!clothingImage && (
            <p className="text-sm text-gray-500 text-center">
              Tip: use "Try On" on a product in the Shop tab to bring a top here.
            </p>
          )}

          {error && <div className="text-red-500 text-center">{error}</div>}
          <div className="flex justify-center space-x-4">
            <button
              onClick={handleTryOn}
              disabled={isLoading || !humanImage || !clothingImage}
              className="bg-pink-500 text-white px-8 py-3 rounded-xl font-semibold hover:bg-pink-600 transition-colors disabled:opacity-50 flex items-center space-x-2"
            >
              {isLoading ? <RefreshCw className="animate-spin" size={20} /> : <Wand2 size={20} />}
              <span>{isLoading ? 'Generating...' : 'Generate'}</span>
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
          <div className="grid grid-cols-3 gap-6 max-w-3xl mx-auto items-end">
            {[
              { src: humanImageUrl, label: 'Photo' },
              { src: clothingImageUrl, label: 'Top' },
              { src: resultImage, label: 'Try-on' },
            ].map(({ src, label }) => (
              <figure key={label}>
                {src && <img src={src} alt={label} className="mx-auto rounded-2xl shadow-lg max-h-[420px] w-full object-contain bg-white" />}
                <figcaption className="mt-2 text-sm text-gray-600">{label}</figcaption>
              </figure>
            ))}
          </div>
          <p className="mt-4 text-xs text-gray-500">DM-VTON generates at 192 x 256, so the result is shown enlarged.</p>
          <div className="flex justify-center mt-6 space-x-4">
            <button
              onClick={() => setResultImage(null)}
              className="bg-pink-500 text-white px-8 py-3 rounded-xl font-semibold hover:bg-pink-600 transition-colors"
            >
              Try Another Top
            </button>
            <button
              onClick={resetTryOn}
              className="bg-gray-200 text-gray-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-300 transition-colors"
            >
              Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
