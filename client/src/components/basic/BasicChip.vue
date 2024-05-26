<template>
  <v-chip class="chip on-background-secondary-color text-color p4">
    {{content}}
  </v-chip>
</template>

<style scoped>
  .chip {
    transition: 600ms;
  }
</style>

<script>
export default {
  name: "BasicChip",
  props: {
    content: {
      type: String,
      default: "",
    }
  }
}
</script>