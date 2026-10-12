<script setup lang="ts">
import type { Species } from "../types";

const query = defineModel<string>({ required: true });

const props = defineProps<{
  matches: Species[];
  highlight: number;
  note: string;
}>();

const emit = defineEmits<{
  input: [value: string];
  move: [step: number];
  choose: [item: Species];
  submit: [];
  escape: [];
}>();

function onInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  query.value = value;
  emit("input", value);
}

function onKeydown(event: KeyboardEvent) {
  if (props.matches.length === 0) {
    return;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    emit("move", 1);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    emit("move", -1);
  } else if (event.key === "Escape") {
    emit("escape");
  } else if (event.key === "Enter") {
    event.preventDefault();
    emit("submit");
  }
}
</script>

<template>
  <form class="search" role="search" @submit.prevent="emit('submit')">
    <label for="q">宝可梦名称</label>
    <input
      id="q"
      :value="query"
      type="search"
      autocomplete="off"
      placeholder="例如：皮卡"
      role="combobox"
      aria-autocomplete="list"
      :aria-expanded="matches.length > 0"
      aria-controls="suggestions"
      @input="onInput"
      @keydown="onKeydown"
    />
    <Transition name="suggest">
      <ul v-if="matches.length" id="suggestions" class="suggestions" role="listbox">
        <li v-for="(item, index) in matches" :key="item.en">
          <button
            type="button"
            role="option"
            :aria-selected="index === highlight"
            @click="emit('choose', item)"
            @mouseenter="emit('move', index - highlight)"
          >
            {{ item.zh }}（{{ item.en }}）
          </button>
        </li>
      </ul>
    </Transition>
    <p v-if="note" class="note">{{ note }}</p>
  </form>
</template>
