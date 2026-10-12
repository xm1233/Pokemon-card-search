import { ref } from "vue";
import { ApiError, fetchCard, fetchCards, fetchSpecies } from "./api";
import type { CardDetail, CardSummary, Species } from "./types";

const UNAVAILABLE = "TCGdex 暂时查不到，请稍后再试";

export function useCatalog() {
  const query = ref("");
  const matches = ref<Species[]>([]);
  const highlight = ref(0);
  const note = ref("");
  const selected = ref<Species | null>(null);
  const page = ref(1);
  const totalPages = ref(0);
  const total = ref(0);
  const cards = ref<CardSummary[]>([]);
  const showResults = ref(false);
  const status = ref("");
  const statusError = ref(false);
  const detail = ref<CardDetail | null>(null);
  const detailOpen = ref(false);

  let suggestTimer = 0;
  let suggestToken = 0;
  let cardsToken = 0;

  function setStatus(message: string, error = false) {
    status.value = message;
    statusError.value = error;
  }

  function hideSuggestions() {
    matches.value = [];
    highlight.value = 0;
  }

  async function loadSuggestions() {
    const current = query.value.trim();
    if (!current) {
      hideSuggestions();
      note.value = "";
      return;
    }
    const token = ++suggestToken;
    try {
      const data = await fetchSpecies(current);
      if (token !== suggestToken || query.value.trim() !== current) {
        return;
      }
      matches.value = data.items;
      highlight.value = 0;
      if (data.total === 0) {
        note.value = "没有找到这个名字，请继续输入";
      } else if (data.total > data.items.length) {
        note.value = "只显示前 30 个，请继续输入";
      } else {
        note.value = "";
      }
    } catch (error) {
      if (token !== suggestToken) {
        return;
      }
      hideSuggestions();
      note.value = error instanceof ApiError ? error.message : "暂时查不到物种，请再试一次";
    }
  }

  function onQueryInput(value: string) {
    query.value = value;
    if (selected.value && value.trim() !== selected.value.zh) {
      selected.value = null;
      showResults.value = false;
      setStatus("");
    }
    window.clearTimeout(suggestTimer);
    suggestTimer = window.setTimeout(loadSuggestions, 150);
  }

  function moveHighlight(step: number) {
    if (matches.value.length === 0) {
      return;
    }
    highlight.value = Math.min(
      matches.value.length - 1,
      Math.max(0, highlight.value + step),
    );
  }

  function chooseHighlighted() {
    const item = matches.value[highlight.value];
    if (item) {
      choose(item);
    }
  }

  function choose(item: Species) {
    selected.value = item;
    query.value = item.zh;
    hideSuggestions();
    note.value = "";
    void loadCards(1);
  }

  async function loadCards(nextPage: number) {
    if (!selected.value) {
      return;
    }
    const token = ++cardsToken;
    const species = selected.value;
    page.value = nextPage;
    setStatus("正在查找卡牌…");
    showResults.value = false;
    detailOpen.value = false;
    try {
      const data = await fetchCards(species.en, nextPage);
      if (token !== cardsToken) {
        return;
      }
      if (data.total === 0) {
        cards.value = [];
        total.value = 0;
        totalPages.value = 0;
        setStatus("这只宝可梦在 TCGdex 英文卡库里没有匹配结果");
        return;
      }
      page.value = data.page;
      totalPages.value = data.pages;
      total.value = data.total;
      cards.value = data.items;
      setStatus("");
      showResults.value = true;
    } catch (error) {
      if (token !== cardsToken) {
        return;
      }
      setStatus(error instanceof ApiError ? error.message : UNAVAILABLE, true);
    }
  }

  async function openDetail(cardId: string | number) {
    setStatus("正在打开卡牌…");
    try {
      detail.value = await fetchCard(cardId);
      detailOpen.value = true;
      setStatus("");
    } catch (error) {
      setStatus(error instanceof ApiError ? error.message : UNAVAILABLE, true);
    }
  }

  function closeDetail() {
    detailOpen.value = false;
  }

  return {
    query,
    matches,
    highlight,
    note,
    selected,
    page,
    totalPages,
    total,
    cards,
    showResults,
    status,
    statusError,
    detail,
    detailOpen,
    onQueryInput,
    moveHighlight,
    chooseHighlighted,
    choose,
    loadCards,
    openDetail,
    closeDetail,
    hideSuggestions,
  };
}
