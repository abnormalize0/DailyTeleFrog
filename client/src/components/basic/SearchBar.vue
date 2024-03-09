<template>
  <v-text-field 
    label="Поиск" 
    class="search-bar text-secondary-color"
    variant="outlined"
    hide-details
    flat
    :append-inner-icon="mdi-magnify"
  >
  </v-text-field>
</template>

<style scoped>
  #input-usage .v-input__prepend-outer,
  #input-usage .v-input__append-outer,
  #input-usage .v-input__slot,
  #input-usage .v-messages {
    border: 1px dashed rgba(0,0,0, .4);
  }
  .search-bar {
    width: 600px;
    height: 44px;
  }
  .search-bar >>> .v-field {
    border-radius: 10px !important;
  }
</style>

<script>
  export default {
    name: "SearchBar",
    data () {
      return {
        text: '',
      }
    },
    methods: {
      appendIconCallback () {},
      prependIconCallback () {},
    },
  }
</script>