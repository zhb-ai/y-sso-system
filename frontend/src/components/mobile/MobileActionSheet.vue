<template>
  <Teleport to="body">
    <div
      v-if="present"
      class="mobile-sheet"
      :class="{ 'is-active': active, 'is-closing': closing }"
      @keydown.esc.prevent="close"
    >
      <div class="mobile-sheet__mask" @click="close"></div>
      <div
        ref="panelRef"
        class="mobile-sheet__panel"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        @transitionend="onPanelEnd"
      >
        <div class="mobile-sheet__grip"></div>
        <div class="mobile-sheet__head">
          <div>
            <h3>{{ title }}</h3>
            <p v-if="subtitle">{{ subtitle }}</p>
          </div>
          <button type="button" class="mobile-sheet__close" aria-label="关闭" @click="close">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        <div class="mobile-sheet__body">
          <slot>
            <button
              v-for="(item, index) in items"
              :key="item.key || item.label || index"
              type="button"
              class="mobile-sheet__item"
              :class="{ 'is-danger': item.danger }"
              :disabled="item.disabled"
              @click="selectItem(item)"
            >
              <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </button>
          </slot>
        </div>
        <div v-if="$slots.footer" class="mobile-sheet__foot">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import { Close } from "@element-plus/icons-vue";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: "" },
  subtitle: { type: String, default: "" },
  items: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:modelValue", "select"]);

const present = ref(false);
const active = ref(false);
const closing = ref(false);
const panelRef = ref(null);
let closeTimer = 0;

const reduceMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const lockScroll = (locked) => {
  document.body.classList.toggle("mobile-sheet-open", locked);
};

const openSheet = async () => {
  window.clearTimeout(closeTimer);
  closing.value = false;
  present.value = true;
  await nextTick();
  requestAnimationFrame(() => {
    active.value = true;
  });
};

const close = () => {
  emit("update:modelValue", false);
};

const finishClose = () => {
  if (props.modelValue) return;
  present.value = false;
  closing.value = false;
  lockScroll(false);
};

const onPanelEnd = (event) => {
  if (event.target !== panelRef.value || event.propertyName !== "transform") return;
  if (!active.value) finishClose();
};

const selectItem = (item) => {
  if (item.disabled) return;
  close();
  item.onClick?.();
  emit("select", item);
};

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      lockScroll(true);
      openSheet();
      return;
    }
    active.value = false;
    closing.value = true;
    window.clearTimeout(closeTimer);
    closeTimer = window.setTimeout(finishClose, reduceMotion() ? 0 : 460);
  },
);

onBeforeUnmount(() => {
  window.clearTimeout(closeTimer);
  lockScroll(false);
});
</script>
