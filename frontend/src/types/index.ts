export interface Product {
  id: string;
  title: string;
  price: number;
  image: string;
  category: 'tops' | 'tshirts' | 'shirts' | 'hoodies' | 'jackets';
  size: string[];
  color: string;
  company: string;
}

export interface CartItem extends Product {
  selectedSize: string;
  quantity: number;
}

export interface User {
  id: string;
  name: string;
}

export interface GamePlayer {
  id: string;
  name: string;
  selectedOutfit?: Product[];
  score: number;
}

export interface GameSession {
  sessionId: string;
  players: GamePlayer[];
  timeLeft: number;
  phase: 'selecting' | 'rating' | 'results';
  currentRound: number;
}

export interface DesignPrompt {
  prompt: string;
  generatedImage?: string;
  timestamp: Date;
}

export interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}