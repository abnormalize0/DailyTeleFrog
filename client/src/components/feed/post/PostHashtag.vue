<template>
  <section class="post-hashtag on-background-secondary-color">
    <p class="p4">#{{ content }}</p>
  </section>
</template>

<style scoped>
  .post-hashtag {
    height: 24px;
    border-radius: 900px;
    padding: 6px 10px;
  }

  .post-hashtag:hover {
    cursor: pointer;
  }
</style>

<script>
export default {
  name: "post-hashtag",
  props: {
    content: String,
  },
};
</script>
