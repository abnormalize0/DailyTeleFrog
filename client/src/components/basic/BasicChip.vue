<template>
  <v-chip class="on-background-secondary-color text-color p4">
    {{content}}
  </v-chip>
</template>

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