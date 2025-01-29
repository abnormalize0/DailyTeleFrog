<template>
  <div class="carousel d-flex flex-column">
    <div class="d-flex flex-row carousel-images">
      <img
        v-for="(image, index) in imgs"
        :key="index"  
        :src='image'
        :class="{ active: index === currentIndex }"
        alt="Carousel Image"
      />
    </div>

    <div v-if="imgs.length > 1" class="d-flex flex-row carousel-controls">
      <label
        v-for="(_, index) in imgs"
        :key="index"
        class="radio-label"
      >
      </label>
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
  overflow: hidden;
}

img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.5s ease;
}

img.active {
  opacity: 1;
}

.carousel-controls {
  align-self: center;
  gap: 5px;
}

.radio-label {
  width: 10px;
  height: 10px;
  border-radius: 100%;
  border-width: 1.5px;
  border: var(--primary-second-color);
  cursor: pointer;
  display: inline-block;
  transition: background-color 0.3s;
}

.radio-label input[type="radio"]:checked + .radio-label {
  background-color: var(--primary-color) !important;
  border: var(--primary-color);
}

.radio-label input[type="radio"] {
  display: none;
}

/* .carousel-images {
  position: relative;
  width: 90%; 
  height: 300px;
  overflow: hidden;
}

.carousel-images img {
  position: absolute;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.5s ease;
}

.carousel-images img.active {
  opacity: 1;
} */
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
  }
}
</script>
