<template>
  <div class="d-flex align-center search-bar primary-border primary-rounded">
    <input class="search" placeholder="Search" type="text" onfocus="this.placeholder = ''"
      onblur="this.placeholder = 'Search'">
    <button class="container-icon">
      <i class="search-text-secondary-color-icon"></i>
    </button>
  </div>
</template>

<style scoped>
  .search-bar {
    width: 600px;
    height: 44px;
    padding: 10px 30px;
    background-color: transparent;
  }
  .search-bar:hover,
  .search-bar:focus-within,
  .search-bar:active {
    background-color: var(--text-color);
  }
  .container-icon {
    all: unset;
    cursor: pointer;
  }
  .search {
    width: 100%;
    outline: 0;
    color: var(--text-secondary-color);
  }
  .search::-webkit-input-placeholder {
    font-family: var(--family-name);
    font-size: 14px !important;
    letter-spacing: 0 !important;  
  }
  .search:-ms-input-placeholder {
    font-family: var(--family-name);
    font-size: 14px !important;
    letter-spacing: 0 !important;  
  }
  .search:-moz-placeholder {
    font-family: var(--family-name);
    font-size: 14px !important;
    letter-spacing: 0 !important;  
  }
  .search::-moz-placeholder {
    font-family: var(--family-name);
    font-size: 14px !important;
    letter-spacing: 0 !important;  
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