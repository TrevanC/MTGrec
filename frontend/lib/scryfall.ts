import { ScryfallCard } from './types';

export function getCardImageUrl(card: ScryfallCard, size: 'small' | 'normal' | 'large' = 'normal'): string {
  // Handle double-faced cards
  if (card.card_faces && card.card_faces.length > 0) {
    return card.card_faces[0].image_uris?.[size] || '';
  }

  // Handle regular cards
  return card.image_uris?.[size] || '';
}

export function getCardPrice(card: ScryfallCard): number {
  const usdPrice = card.prices?.usd;
  return usdPrice ? parseFloat(usdPrice) : 0;
}

export function formatPrice(price: number): string {
  if (price === 0) return 'N/A';
  return `$${price.toFixed(2)}`;
}

export function getColorIdentitySymbols(colorIdentity: string[]): string {
  const symbols: Record<string, string> = {
    W: '⚪',
    U: '🔵',
    B: '⚫',
    R: '🔴',
    G: '🟢',
  };

  return colorIdentity.map(color => symbols[color] || color).join('');
}

export function getManaValue(card: ScryfallCard): number {
  return card.cmc || 0;
}

export function isCommander(card: ScryfallCard): boolean {
  const typeLine = card.type_line.toLowerCase();
  const oracleText = card.oracle_text?.toLowerCase() || '';

  return (
    (typeLine.includes('legendary') && typeLine.includes('creature')) ||
    oracleText.includes('can be your commander') ||
    oracleText.includes('as a second commander')
  );
}

export function getMainCardFace(card: ScryfallCard) {
  if (card.card_faces && card.card_faces.length > 0) {
    return {
      name: card.card_faces[0].name,
      type_line: card.card_faces[0].type_line,
      oracle_text: card.card_faces[0].oracle_text,
      colors: card.card_faces[0].colors,
    };
  }

  return {
    name: card.name,
    type_line: card.type_line,
    oracle_text: card.oracle_text,
    colors: card.colors,
  };
}