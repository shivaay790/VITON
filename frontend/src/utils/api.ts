import { Product } from '../types';
import { BACKEND_URL } from "../config";

// Mock API functions
export const api = {
  async recommend(top_k: number = 4): Promise<Product[]> {
    const res = await fetch(`${BACKEND_URL}/recommend?top_k=${top_k}`);
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    const data = await res.json();
    // Convert image URLs to Product objects
    return data.images.map((url: string) => ({
      id: url,
      title: url.split('/').pop() || '',
      image: `${BACKEND_URL}${url}`,
      price: 0,
      category: 'tops',
      company: 'Dataset',
      color: '',
      size: [],
    }));
  },

  async filter(params: {
    category?: string;
    color?: string;
    company?: string;
    priceMax?: number;
    page?: number;
    pageSize?: number;
  }): Promise<string[]> {
    const query = new URLSearchParams();
    query.append('session_id', 'store');
    if (params.page) query.append('page', params.page.toString());
    if (params.pageSize) query.append('page_size', params.pageSize.toString());
    if (params.category) query.append('category', params.category);
    if (params.color) query.append('color', params.color);
    if (params.company) query.append('company', params.company);
    if (params.priceMax) query.append('priceMax', params.priceMax.toString());
    const res = await fetch(`${BACKEND_URL}/clothes_list?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to filter tops');
    const data = await res.json();
    return data.clothes;
  },

  async tryOn(humanImage: File, clothingImage?: File, cloth?: string): Promise<string> {
    const formData = new FormData();
    formData.append('person_image', humanImage);
    if (clothingImage) {
      formData.append('cloth_image', clothingImage);
    }
    if (cloth) {
      formData.append('cloth', cloth);
    }
    const res = await fetch(`${BACKEND_URL}/viton_preview_upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to generate try-on');
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  },

  async design(prompt: string): Promise<string> {
    const res = await fetch(`${BACKEND_URL}/design`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(prompt),
    });
    if (!res.ok) throw new Error('Failed to generate design');
    const data = await res.json();
    return data.image;
  },

  async getTops({ session_id = 'store', page = 1, pageSize = 50 } = {} as { session_id?: string; page?: number; pageSize?: number }): Promise<string[]> {
    const url = `${BACKEND_URL}/clothes_list?session_id=${session_id}&page=${page}&page_size=${pageSize}`;
    console.log('🔍 Frontend getTops request:', { session_id, page, pageSize });
    console.log('🔍 Making request to:', url);
    
    const res = await fetch(url);
    if (!res.ok) {
      console.error('❌ GetTops request failed:', res.status, res.statusText);
      throw new Error('Failed to fetch tops');
    }
    
    const data = await res.json();
    console.log('🔍 GetTops response:', data);
    return data.clothes;
  },

  async searchClothes(params: { query?: string; category?: string; company?: string; color?: string; }): Promise<string[]> {
    // Combine all filters into a single string
    let combinedQuery = '';
    if (params.query) combinedQuery += params.query + ' ';
    if (params.category) combinedQuery += params.category + ' ';
    if (params.company) combinedQuery += params.company + ' ';
    if (params.color) combinedQuery += params.color + ' ';
    combinedQuery = combinedQuery.trim();
    if (!combinedQuery) combinedQuery = 'all';
    
    console.log('🔍 Frontend search params:', params);
    console.log('🔍 Combined query:', combinedQuery);
    
    const query = new URLSearchParams();
    if (combinedQuery) query.append('query', combinedQuery);
    
    const url = `${BACKEND_URL}/search_clothes?${query.toString()}`;
    console.log('🔍 Making request to:', url);
    
    const res = await fetch(url);
    if (!res.ok) {
      console.error('❌ Search request failed:', res.status, res.statusText);
      throw new Error('Failed to search clothes');
    }
    
    const data = await res.json();
    console.log('🔍 Search response:', data);
    return data.clothes;
  },

  async ping(): Promise<{ message: string }> {
    const res = await fetch(`${BACKEND_URL}/api/ping`);
    if (!res.ok) throw new Error('Backend not reachable');
    return res.json();
  },

  async startGame({ num_players, num_rounds, timer, n_clothes = 10 }: { num_players: number; num_rounds: number; timer: number; n_clothes?: number }) {
    const res = await fetch(`${BACKEND_URL}/start_game`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_players, num_rounds, timer, n_clothes }),
    });
    if (!res.ok) throw new Error('Failed to start game');
    return res.json();
  },

  async pick({ session_id, round_num, player, picks }: { session_id: string; round_num: number; player: string; picks: any }) {
    const res = await fetch(`${BACKEND_URL}/pick`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, round_num, player, picks }),
    });
    if (!res.ok) throw new Error('Failed to submit pick');
    return res.json();
  },

  async rank({ session_id, round_num, player, ranking }: { session_id: string; round_num: number; player: string; ranking: any }) {
    const res = await fetch(`${BACKEND_URL}/rank`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, round_num, player, ranking }),
    });
    if (!res.ok) throw new Error('Failed to submit ranking');
    return res.json();
  },

  async getLeaderboard(session_id: string) {
    const res = await fetch(`${BACKEND_URL}/leaderboard?session_id=${encodeURIComponent(session_id)}`);
    if (!res.ok) throw new Error('Failed to fetch leaderboard');
    return res.json();
  },

  async getReceivedClothes(session_id: string, round_num: number, player: string) {
    const params = new URLSearchParams({
      session_id,
      round_num: String(round_num),
      player
    });
    const res = await fetch(`${BACKEND_URL}/received_clothes?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch received clothes');
    return res.json();
  },

  async getAvailableClothes(session_id: string, round_num: number, target_player: string) {
    const params = new URLSearchParams({
      session_id,
      round_num: String(round_num),
      target_player
    });
    const res = await fetch(`${BACKEND_URL}/available_clothes?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch available clothes');
    return res.json();
  },

  async getDetailedLeaderboard(session_id: string) {
    const res = await fetch(`${BACKEND_URL}/detailed_leaderboard?session_id=${encodeURIComponent(session_id)}`);
    if (!res.ok) throw new Error('Failed to fetch detailed leaderboard');
    return res.json();
  }
};