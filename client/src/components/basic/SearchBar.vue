<template>
  <div class="d-flex align-center search-bar primary-border primary-rounded">
    <input class="input-search" placeholder="Search" type="text" onfocus="this.placeholder = ''"
      onblur="this.placeholder = 'Search'">
    <button class="container-button-icon">
      <i class="search-text-secondary-color-icon"></i>
    </button>
  </div>
</template>

<style scoped>
  .search-bar {
    width: 558px;
    height: 44px;
    padding: 10px 30px;
    background-color: transparent;
    caret-color: var(--text-secondary-color);
    transition: 600ms;
  }
  .search-bar:hover,
  .search-bar:focus-within,
  .search-bar:active {
    background-color: var(--background-secondary-color);
  }
  .container-button-icon {
    all: unset;
    cursor: pointer;
  }
  .input-search {
    width: 100%;
    outline: 0;
    color: var(--text-secondary-color);
  }
  .input-search::-webkit-input-placeholder,
  .input-search:-ms-input-placeholder,
  .input-search:-moz-placeholder,
  .input-search::-moz-placeholder {
    font-family: var(--family-name);
    font-size: 14px !important;
    letter-spacing: 0 !important;  
  }
</style>

<script>
export default {
  name: "SearchBar",
}
</script>