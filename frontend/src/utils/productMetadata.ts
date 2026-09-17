import { API_BASE_URL } from '../config';
import { Product } from '../types';
import { companies, colors } from '../data/constants';

const productCategories: Product['category'][] = ['tshirts', 'shirts', 'hoodies', 'jackets'];

const productPriceBuckets = Array.from(
  new Set([
    ...Array.from({ length: 41 }, (_, i) => i * 50),
    ...Array.from({ length: 40 }, (_, i) => 25 + i * 50),
    ...Array.from({ length: 40 }, (_, i) => 49 + i * 50),
    ...Array.from({ length: 20 }, (_, i) => 99 + i * 100),
  ].filter((value) => value >= 0 && value <= 2000))
).sort((a, b) => a - b);

function stableHash(text: string): number {
  let value = 0;
  const lower = text.toLowerCase();
  for (let i = 0; i < lower.length; i += 1) {
    value = (value * 131 + lower.charCodeAt(i) * (i + 1)) % 1000000007;
  }
  return value;
}

export function filenameToProduct(filename: string): Product {
  const base = filename.replace(/\.[^/.]+$/, '');
  const hash = stableHash(base);
  const company = companies[hash % companies.length];
  const category = productCategories[Math.floor(hash / 3) % productCategories.length];
  const color = colors[Math.floor(hash / 7) % colors.length];
  const price = productPriceBuckets[Math.floor(hash / 11) % productPriceBuckets.length];

  return {
    id: filename,
    title: base.replace(/[_-]+/g, ' '),
    image: `${API_BASE_URL}/clothes/${filename}`,
    price,
    category,
    company,
    color,
    size: ['S', 'M', 'L', 'XL'],
  };
}
