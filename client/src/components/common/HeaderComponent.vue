<template>
  <div class="grid-container header">
    <img src="../../assets/Logo.png" alt="Logo" />
    <SearchBar/>
    <BasicPrimaryButton content="Войти" class="button-position"/>
  </div>
</template>

<style scoped>
  .header {
    height: 72px;
    align-content: center;
  }
  .button-position {
    grid-column: 12
  }
</style>

<script>
import BasicPrimaryButton from '../basic/BasicPrimaryButton.vue';
import SearchBar from '../basic/SearchBar.vue';

export default {
  name: "HeaderComponent",
  components: {
    BasicPrimaryButton,
    SearchBar
  }
}
</script>