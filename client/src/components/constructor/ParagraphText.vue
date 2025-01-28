<template>
  <div 
    class="p2 text-color"
    :class="applyState"
  >
    {{ content }}
  </div>
</template>

<style scoped>
.italic {
  font-style: italic;
}
.bold {
  font-weight: bold;
}
.strikethrough {
  text-decoration: line-through;
}
.underline {
  text-decoration: underline;
}
</style>

<script>
import { ParagraphState } from '@/enum/ParagraphState';

export default {
  name: "ParagraphText",
  props: {
    content: {
      type: String,
      default: "",
    },
    states: {
      content: {
        type: Array,
        default: () => [],
      },
      validator(states)  {
        return (
          Array.isArray(states.content) &&
            states.content.every((state) => Object.values(ParagraphState).includes(state))
        )
      }
    }
  },
  computed: {
    applyState() {
      let computedClass = "";
      this.states?.forEach(state => {
        if (state === ParagraphState.ITALIC) {
          computedClass += computedClass ? " italic" : "italic";
        } 
        if (state === ParagraphState.BOLD) {
          computedClass += computedClass ? " bold" : "bold";
        }
        if (state === ParagraphState.STRIKETHROUGH) {
          computedClass += computedClass ? " strikethrough" : "strikethrough";
        }
        if (state === ParagraphState.UNDERLINE) {
          computedClass += computedClass ? " underline" : "underline";
        }
      });
      return computedClass;
    }
  }
}
</script>