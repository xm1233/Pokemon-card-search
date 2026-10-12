import type { ApiFailure, CardDetail, CardsPage, SpeciesResponse } from "./types";

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function readJson<T>(response: Response, fallback: string): Promise<T> {
  const data = (await response.json().catch(() => ({}))) as T & ApiFailure;
  if (!response.ok) {
    throw new ApiError(data.detail || fallback);
  }
  return data;
}

export function fetchSpecies(query: string): Promise<SpeciesResponse> {
  return fetch("/api/species?q=" + encodeURIComponent(query)).then((response) =>
    readJson<SpeciesResponse>(response, "暂时查不到物种，请再试一次"),
  );
}

export function fetchCards(englishName: string, page: number): Promise<CardsPage> {
  const params = new URLSearchParams({
    en: englishName,
    page: String(page),
  });
  return fetch("/api/cards?" + params.toString()).then((response) =>
    readJson<CardsPage>(response, "TCGdex 暂时查不到，请稍后再试"),
  );
}

export function fetchCard(cardId: string | number): Promise<CardDetail> {
  return fetch("/api/cards/" + encodeURIComponent(String(cardId))).then((response) =>
    readJson<CardDetail>(response, "TCGdex 暂时查不到，请稍后再试"),
  );
}
