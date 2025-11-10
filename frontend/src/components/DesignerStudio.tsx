import React, { useState } from 'react';
import { Palette, Wand2, Download, Heart } from 'lucide-react';
import { api } from '../utils/api';
import { DesignPrompt } from '../types';

export function DesignerStudio() {
  const [prompt, setPrompt] = useState('');
  const [designs, setDesigns] = useState<DesignPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDesign = async () => {
    if (!prompt.trim()) {
      setError('Please describe your desired outfit');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const generatedImage = await api.design(prompt);
      const newDesign: DesignPrompt = {
        prompt,
        generatedImage,
        timestamp: new Date()
      };
      setDesigns(prev => [newDesign, ...prev]);
      setPrompt('');
    } catch (err) {
      setError('Failed to generate design. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const examplePrompts = [
    "Design an Adidas-style athletic t-shirt with bold stripes",
    "Create a vintage Levi's denim jacket with distressed details",
    "Design a modern Puma hoodie with geometric patterns",
    "Create an elegant HUGO dress shirt with subtle textures"
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4 flex items-center justify-center">
          <Palette className="mr-3 text-pink-500" size={32} />
          AI Fashion Designer
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Describe your dream outfit and watch our AI bring it to life. Get creative with colors, patterns, and styles!
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-8">
        <label htmlFor="design-prompt" className="block text-sm font-medium text-gray-700 mb-3">
          Describe your desired outfit
        </label>
        <textarea
          id="design-prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., Design an Adidas-style athletic t-shirt with bold stripes..."
          className="w-full p-4 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent"
          rows={4}
        />

        {/* Example Prompts */}
        <div className="mt-4">
          <p className="text-sm text-gray-500 mb-2">Try these examples:</p>
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((example, index) => (
              <button
                key={index}
                onClick={() => setPrompt(example)}
                className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-lg transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleDesign}
          disabled={!prompt.trim() || isLoading}
          className="mt-4 w-full bg-gradient-to-r from-pink-500 to-purple-500 text-white py-3 rounded-xl font-semibold hover:from-pink-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Designing...</span>
            </>
          ) : (
            <>
              <Wand2 size={18} />
              <span>Design It</span>
            </>
          )}
        </button>
      </div>

      {/* Designs Gallery */}
      {designs.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Your Designs</h2>
          <div className="grid gap-6">
            {designs.map((design, index) => (
              <div key={index} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="md:flex">
                  <div className="md:w-1/2">
                    <img
                      src={design.generatedImage}
                      alt="Generated design"
                      className="w-full h-64 md:h-80 object-cover"
                    />
                  </div>
                  <div className="md:w-1/2 p-6 flex flex-col justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3">Design Prompt</h3>
                      <p className="text-gray-600 mb-4">{design.prompt}</p>
                      <p className="text-sm text-gray-400">
                        Created {design.timestamp.toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex space-x-3 mt-4">
                      <button className="flex-1 bg-pink-500 text-white py-2 px-4 rounded-lg font-medium hover:bg-pink-600 transition-colors flex items-center justify-center space-x-2">
                        <Heart size={16} />
                        <span>Save</span>
                      </button>
                      <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2">
                        <Download size={16} />
                        <span>Download</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}