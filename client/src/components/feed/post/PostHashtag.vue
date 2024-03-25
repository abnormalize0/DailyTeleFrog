<template>
  <section class="post-hashtag on-background-secondary-color">
    <p class="p4">#{{ content }}</p>
  </section>
</template>
<script>
export default {
  name: "post-hashtag",
  components: {},
  props: {
    content: String,
  },
  data() {
    return {};
  },
  computed: {},
  mounted() {},
  methods: {},
};
</script>
<style scoped>
.post-hashtag {
  height: 28px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.p4 {
  padding: 8px;
}

.post-hashtag:hover {
  cursor: pointer;
}
</style>
