<template>
  <div class="post-link primary-rounded d-flex flex-column">
    <div class="h2 text-color">
      {{ preheader }}
    </div>
    <div class="d-flex flex-column middle">
      <div class="p3 text-color">
        {{ text }}
      </div>
      <img 
        :src="image"
      />
    </div>
  </div>
</template>

<style scoped>
.post-link {
  width: 240px;
  padding: 15px;
  border: 1px solid var(--text-secondary-color);
  gap: 10px;
}

.middle {
  gap: 10px;
}

.middle div {
  height: 105px;
  text-overflow: ellipsis;
  overflow-y: hidden;
}

.middle img {
  height: 144px;
}
</style>

<script>
export default {
  name: "LinkPost",
  props: {
    preheader: {
      type: String,
      default: "",
    },
    text: {
      type: String,
      default: "",
    },
    image: {
      type: String,
      default: "",
    },
  },
}
</script>