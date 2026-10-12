<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import type { Attack, CardDetail } from "../types";

const props = defineProps<{
  open: boolean;
  card: CardDetail | null;
}>();

const emit = defineEmits<{
  close: [];
}>();

const dialog = ref<HTMLDialogElement | null>(null);

watch(
  () => props.open,
  async (open) => {
    await nextTick();
    const element = dialog.value;
    if (!element) {
      return;
    }
    if (open && !element.open) {
      element.showModal();
    }
    if (!open && element.open) {
      element.close();
    }
  },
);

function costText(attack: Attack) {
  return (attack.cost || []).map((type) => type.zh).filter(Boolean).join(" ");
}

function attackHeading(attack: Attack) {
  return [costText(attack), attack.name, attack.damage].filter(Boolean).join(" ");
}

function requestClose() {
  const element = dialog.value;
  if (!element?.open) {
    emit("close");
    return;
  }
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) {
    emit("close");
    return;
  }
  element.classList.add("is-closing");
  const done = (event: AnimationEvent) => {
    if (event.target !== element || event.animationName !== "dialog-out") {
      return;
    }
    element.removeEventListener("animationend", done);
    element.classList.remove("is-closing");
    emit("close");
  };
  element.addEventListener("animationend", done);
}

function onBackdrop(event: MouseEvent) {
  if (event.target === dialog.value) {
    requestClose();
  }
}

function onCancel(event: Event) {
  event.preventDefault();
  requestClose();
}
</script>

<template>
  <dialog ref="dialog" class="detail" @click="onBackdrop" @cancel="onCancel">
    <div class="detail-top">
      <button type="button" @click="requestClose">关闭</button>
    </div>
    <div v-if="card" class="detail-layout">
      <img v-if="card.image" :src="card.image" :alt="card.name" />
      <div>
        <h2>{{ card.name }}</h2>
        <p class="meta">
          套装 {{ card.setName || "—" }}<template v-if="card.localId"> · 编号 {{ card.localId }}</template>
        </p>
        <p v-if="card.rarity" class="meta">稀有度 {{ card.rarity }}</p>
        <p>生命值 {{ card.hp == null ? "—" : card.hp }}</p>
        <p>属性</p>
        <ul class="chips">
          <li v-for="(type, index) in card.types?.length ? card.types : [{ zh: '—' }]" :key="index">
            {{ type.zh }}
          </li>
        </ul>
        <p>招式</p>
        <p v-if="!card.attacks?.length" class="meta">这张卡没有招式</p>
        <article v-for="(attack, index) in card.attacks" :key="index" class="attack">
          <h3>{{ attackHeading(attack) }}</h3>
          <p v-if="attack.effect">{{ attack.effect }}</p>
        </article>
      </div>
    </div>
  </dialog>
</template>
