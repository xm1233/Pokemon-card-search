<script setup lang="ts">
import CardDetail from "./components/CardDetail.vue";
import CardGrid from "./components/CardGrid.vue";
import SearchBox from "./components/SearchBox.vue";
import { useCatalog } from "./useCatalog";

const {
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
} = useCatalog();
</script>

<template>
  <div class="wrap">
    <header class="site arrive">
      <div class="mast">
        <p class="seal">EN</p>
        <h1>宝可梦卡查</h1>
      </div>
    </header>

    <div class="arrive arrive-2">
      <SearchBox
        v-model="query"
        :matches="matches"
        :highlight="highlight"
        :note="note"
        @input="onQueryInput"
        @move="moveHighlight"
        @choose="choose"
        @submit="chooseHighlighted"
        @escape="hideSuggestions"
      />
    </div>

    <p class="status" role="status" :data-kind="statusError ? 'error' : undefined">{{ status }}</p>

    <CardGrid
      v-if="showResults && selected"
      :species="selected"
      :cards="cards"
      :page="page"
      :pages="totalPages"
      :total="total"
      @open="openDetail"
      @page="loadCards"
    />

    <CardDetail :open="detailOpen" :card="detail" @close="closeDetail" />

    <footer>
      卡牌数据来自 <a href="https://tcgdex.dev/">TCGdex</a>
    </footer>
  </div>
</template>
