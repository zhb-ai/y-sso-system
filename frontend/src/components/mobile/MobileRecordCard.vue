<template>
  <article class="m-card">
    <div class="m-card__body" :class="{ 'is-clipped': clipped }">
      <div
        v-for="(field, index) in shownFields"
        :key="field.key || field.label"
        class="m-field"
        :class="{ 'm-field--reveal': expanded && index >= 5 }"
      >
        <span class="m-field__label">{{ field.label }}</span>
        <div class="m-field__value" :class="field.tone">
          <slot name="value" :field="field" :row="row">
            {{ displayValue(field.value) }}
          </slot>
        </div>
      </div>
      <button v-if="clipped" type="button" class="m-card__expand" @click="expanded = true">
        <el-icon><ArrowDown /></el-icon>
        <span>展开更多</span>
      </button>
      <button
        v-else-if="expanded && fields.length > 5"
        type="button"
        class="m-card__fold"
        @click="expanded = false"
      >
        收起
      </button>
    </div>

    <div v-if="actions.length" class="m-card__ops">
      <el-button
        v-for="action in inlineActions"
        :key="action.key || action.label"
        link
        size="small"
        class="m-op"
        :class="{ 'btn-delete': action.danger }"
        :disabled="action.disabled"
        @click="action.onClick?.()"
      >
        <el-icon v-if="action.icon"><component :is="action.icon" /></el-icon>
        {{ action.label }}
      </el-button>
      <el-button v-if="overflowActions.length" link size="small" class="m-op" @click="moreOpen = true">
        <el-icon><MoreFilled /></el-icon>
        更多
      </el-button>
    </div>

    <MobileActionSheet v-model="moreOpen" title="更多操作" :items="overflowActions" />
  </article>
</template>

<script setup>
import { computed, ref } from "vue";
import { ArrowDown, MoreFilled } from "@element-plus/icons-vue";
import MobileActionSheet from "./MobileActionSheet.vue";

const props = defineProps({
  row: { type: Object, default: () => ({}) },
  fields: { type: Array, default: () => [] },
  actions: { type: Array, default: () => [] },
});

const expanded = ref(false);
const moreOpen = ref(false);

const clipped = computed(() => !expanded.value && props.fields.length > 5);
const shownFields = computed(() => (clipped.value ? props.fields.slice(0, 5) : props.fields));
const inlineActions = computed(() =>
  props.actions.length > 3 ? props.actions.slice(0, 2) : props.actions,
);
const overflowActions = computed(() => (props.actions.length > 3 ? props.actions.slice(2) : []));

const displayValue = (value) => {
  if (value === 0 || value === false) return value;
  if (value === undefined || value === null || value === "") return "—";
  return value;
};
</script>
