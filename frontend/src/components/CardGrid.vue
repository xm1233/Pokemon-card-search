<script setup lang="ts">
import { computed } from "vue";
import type { CardSummary, Species } from "../types";

const props = defineProps<{
  species: Species;
  cards: CardSummary[];
  page: number;
  pages: number;
  total: number;
}>();

const emit = defineEmits<{
  open: [id: string | number];
  page: [page: number];
}>();

const pictured = computed(() => props.cards.filter((card) => card.image));
const plain = computed(() => props.cards.filter((card) => !card.image));

function onPageSelect(event: Event) {
  const nextPage = Number((event.target as HTMLSelectElement).value);
  if (nextPage >= 1 && nextPage <= props.pages) {
    emit("page", nextPage);
  }
}
</script>

<template>
  <section class="results">
    <div class="result-head">
      <h2>{{ species.zh }} · {{ species.en }}</h2>
      <p>共 {{ total }} 张</p>
    </div>
    <div v-if="pictured.length" class="grid">
      <button
        v-for="card in pictured"
        :key="card.id"
        type="button"
        class="card-button"
        @click="emit('open', card.id)"
      >
        <img :src="card.image || ''" :alt="card.name" />
        <span class="set-line">套装 {{ card.setName || "—" }}</span>
        <span class="meta">{{ card.localId ? "编号 " + card.localId : "无编号" }}</span>
      </button>
    </div>
    <ul v-if="plain.length" class="plain-list">
      <li v-for="card in plain" :key="card.id">
        <button type="button" class="plain-card" @click="emit('open', card.id)">
          套装 {{ card.setName || "—" }} · {{ card.localId ? "编号 " + card.localId : "无编号" }}
        </button>
      </li>
    </ul>
    <nav class="pager" aria-label="分页">
      <button type="button" class="nav" :disabled="page <= 1" @click="emit('page', page - 1)">
        上一页
      </button>
      <label>
        页码
        <select :value="page" aria-label="选择页码" :disabled="pages <= 1" @change="onPageSelect">
          <option v-for="index in pages" :key="index" :value="index">第 {{ index }} 页</option>
        </select>
      </label>
      <span class="pager-summary">共 {{ pages }} 页</span>
      <button type="button" class="nav" :disabled="page >= pages" @click="emit('page', page + 1)">
        下一页
      </button>
    </nav>
  </section>
</template>
