export interface Species {
  zh: string;
  en: string;
}

export interface SpeciesResponse {
  query: string;
  total: number;
  items: Species[];
}

export interface CardSummary {
  id: string | number;
  name: string;
  localId?: string;
  setName?: string;
  image?: string | null;
}

export interface CardsPage {
  page: number;
  pages: number;
  total: number;
  items: CardSummary[];
}

export interface TypeLabel {
  zh: string;
}

export interface Attack {
  name?: string | null;
  damage?: string | null;
  effect?: string | null;
  cost?: TypeLabel[];
}

export interface CardDetail {
  name: string;
  image?: string | null;
  setName?: string;
  localId?: string | null;
  rarity?: string | null;
  hp?: number | null;
  types?: TypeLabel[];
  attacks?: Attack[];
}

export interface ApiFailure {
  detail?: string;
}
