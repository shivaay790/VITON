import { API_BASE_URL } from '../config';
import { Product } from '../types';
import { filenameToProduct } from './productMetadata';

interface SearchItem {
  id: string;
  score?: number | null;
  metadata?: { brand?: string; company?: string; category?: string; color?: string; price?: number };
}

// FastAPI puts the reason for a failure in `detail`. Surface it rather than a generic message.
async function errorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === 'string') return body.detail;
  } catch {
    // Not JSON, use the fallback.
  }
  return `${fallback} (HTTP ${res.status})`;
}

export const api = {
  async recommend(top_k: number = 4): Promise<Product[]> {
    const res = await fetch(`${API_BASE_URL}/recommend?top_k=${top_k}`);
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    const data = await res.json();
    
    return (data.images as SearchItem[]).map((item) => {
      const base: Product = filenameToProduct(item.id);
      const md = item.metadata || {};
      return {
        ...base,
        company: md.brand || md.company || base.company,
        category: (md.category || base.category).toLowerCase() as Product['category'],
        color: (md.color || base.color).toLowerCase(),
      };
    });
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
    const res = await fetch(`${API_BASE_URL}/clothes_list?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to filter tops');
    const data = await res.json();
    return data.clothes;
  },

  // `cloth` is a shop item's filename. When given, the backend uses that garment's real mask.
  async tryOn(humanImage: File, clothingImage?: File, cloth?: string): Promise<string> {
    const formData = new FormData();
    formData.append('person_image', humanImage);
    if (clothingImage) {
      formData.append('cloth_image', clothingImage);
    }
    if (cloth) {
      formData.append('cloth', cloth);
    }
    const res = await fetch(`${API_BASE_URL}/viton_preview_upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(await errorMessage(res, 'Failed to generate try-on'));
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  },

  async design(prompt: string): Promise<string> {
    const res = await fetch(`${API_BASE_URL}/design`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(prompt),
    });
    if (!res.ok) throw new Error('Failed to generate design');
    const data = await res.json();
    return data.image;
  },

  async getTops({ session_id = 'store', page = 1, pageSize = 50 } = {} as { session_id?: string; page?: number; pageSize?: number }): Promise<string[]> {
    const url = `${API_BASE_URL}/clothes_list?session_id=${session_id}&page=${page}&page_size=${pageSize}`;
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

  async searchClothes(params: {
    query?: string;
    category?: string;
    company?: string;
    color?: string;
    priceMax?: number;
    page?: number;
    pageSize?: number;
  }): Promise<Product[]> {
    const queryText = params.query?.trim();
    const useQuery = queryText && queryText.length > 0 ? queryText : 'all';

    const query = new URLSearchParams();
    query.append('query', useQuery);
    if (params.category) query.append('category', params.category);
    if (params.company) query.append('company', params.company);
    if (params.color) query.append('color', params.color);
    if (typeof params.priceMax === 'number') query.append('priceMax', params.priceMax.toString());
    if (params.page) query.append('page', params.page.toString());
    if (params.pageSize) query.append('page_size', params.pageSize.toString());

    const url = `${API_BASE_URL}/search_clothes?${query.toString()}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error('Failed to search clothes');
    }
    
    const data: { items?: SearchItem[] } = await res.json();
    const items = Array.isArray(data.items) ? data.items : [];
    return items.map((item) => {
      const base: Product = filenameToProduct(item.id);
      const md = item.metadata ?? {};
      return {
        ...base,
        company: md.brand || md.company || base.company,
        category: (md.category || base.category).toLowerCase() as Product['category'],
        color: (md.color || base.color).toLowerCase(),
        price: typeof md.price === 'number' ? md.price : base.price
      };
    });
  },

  async ping(): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/ping`);
    if (!res.ok) throw new Error('Backend not reachable');
    return res.json();
  },

  async startGame({ num_players, num_rounds, timer, n_clothes = 10 }: { num_players: number; num_rounds: number; timer: number; n_clothes?: number }) {
    const res = await fetch(`${API_BASE_URL}/start_game`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_players, num_rounds, timer, n_clothes }),
    });
    if (!res.ok) throw new Error('Failed to start game');
    return res.json();
  },

  async pick({ session_id, round_num, player, picks }: { session_id: string; round_num: number; player: string; picks: Record<string, number> }) {
    const res = await fetch(`${API_BASE_URL}/pick`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, round_num, player, picks }),
    });
    if (!res.ok) throw new Error('Failed to submit pick');
    return res.json();
  },

  async rank({ session_id, round_num, player, ranking }: { session_id: string; round_num: number; player: string; ranking: number[] }) {
    const res = await fetch(`${API_BASE_URL}/rank`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, round_num, player, ranking }),
    });
    if (!res.ok) throw new Error('Failed to submit ranking');
    return res.json();
  },

  async getLeaderboard(session_id: string) {
    const res = await fetch(`${API_BASE_URL}/leaderboard?session_id=${encodeURIComponent(session_id)}`);
    if (!res.ok) throw new Error('Failed to fetch leaderboard');
    return res.json();
  },

  async getReceivedClothes(session_id: string, round_num: number, player: string) {
    const params = new URLSearchParams({
      session_id,
      round_num: String(round_num),
      player
    });
    const res = await fetch(`${API_BASE_URL}/received_clothes?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch received clothes');
    return res.json();
  },

  async getAvailableClothes(session_id: string, round_num: number, target_player: string) {
    const params = new URLSearchParams({
      session_id,
      round_num: String(round_num),
      target_player
    });
    const res = await fetch(`${API_BASE_URL}/available_clothes?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch available clothes');
    return res.json();
  },

  async getDetailedLeaderboard(session_id: string) {
    const res = await fetch(`${API_BASE_URL}/detailed_leaderboard?session_id=${encodeURIComponent(session_id)}`);
    if (!res.ok) throw new Error('Failed to fetch detailed leaderboard');
    return res.json();
  }
};
