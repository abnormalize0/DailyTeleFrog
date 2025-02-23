<template>
  <div class="d-flex flex-row style-modal primary-rounded">
    <Letter :type="ParagraphState.BOLD"/>
    <Letter :type="ParagraphState.ITALIC"/>
    <Letter :type="ParagraphState.UNDERLINE"/>
    <Letter :type="ParagraphState.STRIKETHROUGH"/>
    <Letter :type="ParagraphState.SPOILER"/>
  </div>
</template>

<style scoped>
.style-modal {
  max-width: 116px;
  gap: 5px;
  padding: 8px;
  background-color: var(--background-secondary-color-hover) !important;
}
</style>

<script>
import Letter from "@/components/add-post/text-frame/Letter.vue";
import { ParagraphState } from '@/enum/ParagraphState';

export default {
  name: "StyleModal",
  components: {
    Letter,
  },
  data: () => ({
    ParagraphState,
  })
};
</script>