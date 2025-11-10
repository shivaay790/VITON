import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { ChatMessage } from '../types';

export function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      text: 'Hi! I\'m your fashion assistant. How can I help you find the perfect top today?',
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateBotResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('size') || lowerMessage.includes('sizing')) {
      return 'Our tops come in sizes XS to XXL. For the best fit, I recommend checking our size guide. Most customers find our sizing runs true to size!';
    }
    
    if (lowerMessage.includes('recommend') || lowerMessage.includes('suggest')) {
      return 'Based on current trends, I\'d recommend our Adidas Originals Trefoil T-Shirt or the HUGO Boss Polo Shirt. Both are versatile and stylish! Would you like to see more options?';
    }
    
    if (lowerMessage.includes('brand') || lowerMessage.includes('adidas') || lowerMessage.includes('nike') || lowerMessage.includes('puma')) {
      return 'We carry premium brands including Adidas, Nike, Puma, HUGO, Levi\'s, Champion, Tommy Hilfiger, and Calvin Klein. Each brand has its unique style and quality!';
    }
    
    if (lowerMessage.includes('price') || lowerMessage.includes('cost') || lowerMessage.includes('cheap') || lowerMessage.includes('expensive')) {
      return 'Our tops range from Rs.300 to Rs.10K+. We have options for every budget! T-shirts start around $35-45, while premium shirts and jackets go up to $120.';
    }
    
    if (lowerMessage.includes('color') || lowerMessage.includes('colours')) {
      return 'We have tops in various colors including white, black, navy, gray, blue, red, and green. You can filter by color in our shop to find exactly what you\'re looking for!';
    }
    
    if (lowerMessage.includes('shipping') || lowerMessage.includes('delivery')) {
      return 'We offer free shipping on orders over $75! Standard delivery takes 3-5 business days, and express shipping is available for faster delivery.';
    }
    
    if (lowerMessage.includes('return') || lowerMessage.includes('exchange')) {
      return 'We have a 30-day return policy. Items must be unworn with tags attached. Exchanges are free, and returns are easy through our online portal!';
    }
    
    if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage.includes('hey')) {
      return 'Hello! Welcome to our fashion store. I\'m here to help you find the perfect tops, shirts, hoodies, or jackets. What are you looking for today?';
    }
    
    if (lowerMessage.includes('thank') || lowerMessage.includes('thanks')) {
      return 'You\'re welcome! I\'m always here to help. Feel free to ask if you have any other questions about our products!';
    }
    
    // Default responses
    const defaultResponses = [
      'That\'s a great question! Our collection focuses on premium tops including t-shirts, shirts, hoodies, and jackets from top brands.',
      'I\'d be happy to help you with that! You can browse our collection or use our AI recommendations for personalized suggestions.',
      'Interesting! Let me help you find what you\'re looking for. Have you tried our virtual try-on feature?',
      'Great choice! Our tops are carefully curated from the best brands. Would you like me to recommend something specific?'
    ];
    
    return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    // Simulate typing delay
    setTimeout(() => {
      const botResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: generateBotResponse(inputText),
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botResponse]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center ${
          isOpen 
            ? 'bg-red-500 hover:bg-red-600 rotate-180' 
            : 'bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 hover:scale-110'
        }`}
      >
        {isOpen ? (
          <X className="text-white" size={24} />
        ) : (
          <MessageCircle className="text-white" size={24} />
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-40 w-80 h-96 bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
          {/* Header */}
          <div className="bg-gradient-to-r from-pink-500 to-purple-500 p-4 text-white">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Bot size={18} />
              </div>
              <div>
                <h3 className="font-semibold">Fashion Assistant</h3>
                <p className="text-xs opacity-90">Online now</p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start space-x-2 max-w-[80%] ${message.isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.isUser ? 'bg-pink-500' : 'bg-gray-200'
                  }`}>
                    {message.isUser ? (
                      <User size={12} className="text-white" />
                    ) : (
                      <Bot size={12} className="text-gray-600" />
                    )}
                  </div>
                  <div className={`rounded-2xl px-3 py-2 ${
                    message.isUser 
                      ? 'bg-pink-500 text-white' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    <p className="text-sm">{message.text}</p>
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2 max-w-[80%]">
                  <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                    <Bot size={12} className="text-gray-600" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl px-3 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent text-sm"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputText.trim()}
                className="w-10 h-10 bg-gradient-to-r from-pink-500 to-purple-500 text-white rounded-xl hover:from-pink-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}