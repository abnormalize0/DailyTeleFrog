<template>
  <v-container>
    <v-row>
      <v-text-field
        :label=label
        outlined
        dense
        class="input text-color"
      >
    </v-text-field>
    </v-row>
  </v-container>
</template>

<style scoped>
.input {
  height: 50px !important;
}
</style>

<script>
export default {
  name: "BasicInput",
  props: {
    label: {
      type: String,
      default: "",
    }
  }
}
</script>