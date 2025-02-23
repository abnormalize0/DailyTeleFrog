<template>
  <div class="d-flex align-center search-bar primary-border primary-rounded">
    <button class="container-button-icon">
      <i class="add-icon"></i>
    </button>
    <input class="input-search" placeholder="Напишите что-то, или введите “/” для команд..."
      type="text" onfocus="this.placeholder = ''"
      onblur="this.placeholder = 'Напишите что-то, или введите “/” для команд...'">
    <button class="container-button-icon">
      <i class="trash-icon"></i>
    </button>
  </div>
</template>

<style scoped>
  .add-icon {
    margin-right: 12px;
  }
  .search-bar {
    width: 558px;
    height: 54px;
    padding: 10px 15px;
    background-color: transparent;
    caret-color: var(--text-color);
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
    color: var(--text-color);
  }
  .input-search::-webkit-input-placeholder,
  .input-search:-ms-input-placeholder,
  .input-search:-moz-placeholder,
  .input-search::-moz-placeholder {
    font-family: var(--family-name);
    font-size: 16px !important;
    letter-spacing: 0 !important;  
  }
</style>

<script>
export default {
  name: "SmartInput",
  props: {
    content: String,
  },
};
</script>
