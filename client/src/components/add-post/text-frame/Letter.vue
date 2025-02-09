<template>
  <button 
    class="d-flex letter p2 not-active-color secondary-rounded justify-center align-center" 
    :class="applyStyle"
  >
    {{ this.letter }}
  </button>
</template>

<style scoped>
.letter {
  width: 16px;
  height: 16px;
}

.letter:hover {
  border: 1px solid var(--not-active-color);
}

.letter:focus {
  color: var(--active-color) !important;
}
</style>

<script>
import { ParagraphState } from '@/enum/ParagraphState';

export default {
  name: "Letter",
  props: {
    type: {
      type: ParagraphState,
      default: undefined,
    },
  },
  data: () => ({
    letter: ""
  }),
  computed: {
    applyStyle() {
      if (!this.type) {
        return;
      }
      if (this.type === ParagraphState.BOLD) {
        this.letter = "B";
        return "bold";
      }
      if (this.type === ParagraphState.ITALIC) {
        this.letter = "I";
        return "italic";
      }
      if (this.type === ParagraphState.UNDERLINE) {
        this.letter = "U";
        return "underline";
      }
      if (this.type === ParagraphState.STRIKETHROUGH) {
        this.letter = "S";
        return "strikethrough";
      }
      this.letter = "C";
      return;
    }
  }
}
</script>