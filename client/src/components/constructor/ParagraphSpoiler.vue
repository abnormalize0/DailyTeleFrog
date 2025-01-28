<template>
  <div @click="toggleSpoiler">
    <span 
      class="p2 text-color span-content" 
      ref="spanContent"
      v-show="!noFirstTransition"
    >
      {{ content }}
    </span>
    <div 
      class="hide secondary-rounded" 
      ref="hide" 
      data-testid="hide"
      :class="{ 
        'hide-spoiler': isRevealed, 
        'show-spoiler': !isRevealed,
        'no-transition': noFirstTransition
       }"
      :style="{ 
        maxWidth: maxWidth + 'px', 
        maxHeight: maxHeight + 'px', 
        top: -maxHeight - 2 + 'px'
      }"
    >
      <div
        v-for="(tile, index) in tiles"
        :key="index"
        class="tile"
        :style="{
          opacity: tile.opacity, 
          width: this.tileSize + 'px',
          height: this.tileSize + 'px',
        }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.span-content {
  user-select: none;
}
.hide {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--text-secondary-color);
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  transition: 0.35s;
}

.no-transition {
  transition: none !important;
}

.tile {
  box-sizing: border-box;
  background: var(--text-color);
}

.show-spoiler {
  background: var(--text-secondary-color);
}

.hide-spoiler {
  max-width: 0 !important;
  background: transparent;
}
</style>


<script>
import { ref, nextTick } from "vue";

export default {
  name: "ParagraphSpoler",
  setup() {
    const spanContent = ref(null);
    const hide = ref(null);

    return {
      spanContent,
      hide,
    }
  },
  mounted() {
    document.fonts.ready.then(() => {
      nextTick().then(() => {
        this.calculateMaxWidth();
        this.generateTiles();
        this.noFirstTransition = true;
      });
    })
  },
  data() {
    return {
      isRevealed: false,
      maxWidth: 0,
      maxHeight: 0,
      noFirstTransition: false,
      tiles: [],
      tileSize: 8,
      rows: 0,
      columns: 0
    }
  },
  props: {
    content: {
      type: String,
      default: "",
    },
  },
  methods: {
    generateTiles() {      
      if (this.hide) {
        this.columns = Math.ceil(this.maxWidth / this.tileSize);
        this.rows = Math.ceil(this.maxHeight / this.tileSize)
        this.tiles = Array.from({ length: this.rows * this.columns}, () => ({opacity: Math.random(),}));
      }
    },
    toggleSpoiler() {
      this.isRevealed = !this.isRevealed;
      this.noFirstTransition = this.noFirstTransition ? !this.noFirstTransition : this.noFirstTransition;
    },
    calculateMaxWidth() {
      if (this.spanContent) {
        this.maxWidth = this.spanContent.getBoundingClientRect().width;
        this.maxHeight = this.spanContent.getBoundingClientRect().height;
      }
    }
  },
};
</script>