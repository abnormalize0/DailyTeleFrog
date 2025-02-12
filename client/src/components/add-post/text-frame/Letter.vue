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
      switch(this.type) {
        case ParagraphState.BOLD:
          this.letter = "B";
          return "bold";
        case ParagraphState.ITALIC:
          this.letter = "I";
          return "italic";
        case ParagraphState.UNDERLINE:
          this.letter = "U";
          return "underline";
        case ParagraphState.STRIKETHROUGH:
          this.letter = "S";
          return "strikethrough";
        default:
          this.letter = "C";
          return;
      }
    }
  }
}
</script>