<template>
  <div class="carousel d-flex flex-column">
    <div class="d-flex flex-row carousel-images">
      <img
        v-if="imgs.length > 0"
        :key="'key_' + currentIndex"  
        :src='imgs[currentIndex]'
        class="fade"
        :class="{ active: true }"
        alt="Carousel Image"
      />
    </div>

    <div v-if="imgs.length > 1" class="d-flex flex-row carousel-controls">
      <input
        v-for="(_, index) in imgs"
          type="radio"
          :value="index"
          v-model="currentIndex"
        />
    </div>
  </div>
</template>

<style scoped>
.carousel {
  width: 558px;
  text-align: center;
  gap: 10px;
}

.carousel-images {
  width: 100%;
  min-height: 193px;
  overflow: hidden;
}

img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
}

img.active {
  opacity: 1;
}

.carousel-controls {
  align-self: center;
  gap: 5px;
}

input[type="radio"] {
  appearance: none;
  width: 16px;
  height: 16px;
  border: 1.5px solid var(--primary-second-color);
  border-radius: 50%;
  outline: none;
  cursor: pointer;
  position: relative;
}

input[type="radio"]:checked {
  border-color: var(--primary-first-color);
}

input[type="radio"]:checked::before {
  content: "";
  width: 10px;
  height: 10px;
  background-color: var(--primary-first-color);
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>


<script>
export default {
  name: "ImageCarousel",
  props: {
    imgs: {
      type: Array,
      default: () => [],
    }
  },
  data() {
    return {
      currentIndex: 0,
    }
  },
}
</script>
