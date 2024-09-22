<template>
  <v-btn 
    class="button primary-rounded p-button"
    :class="disabled ? 'disabled' : 'primary-first-color text-color'"
    height="44px"
  >
    {{content}}
  </v-btn>
</template>

<style scoped>
  .button {
    transition: 600ms;
    padding: 10px 16px 10px 16px;
  }
  .disabled {
    background: var(--text-secondary-color);
    color: var(--text-secondary-color-hover);
  }
</style>

<script>
export default {
  name: "BasicPrimaryButton",
  props: {
    content: {
      type: String,
      default: "",
    },
    disabled: {
      type: Boolean,
      default: false
    }
  }
}
</script>