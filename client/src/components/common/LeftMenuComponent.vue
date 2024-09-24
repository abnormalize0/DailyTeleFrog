<template>
  <div class="d-flex flex-column left-menu">
    <div class="d-flex flex-column block-menu">
      <PrependMenuButton label="Моя лента" icon="home-icon"/>
      <PrependMenuButton label="Популярное" icon="popular-icon"/>
      <PrependMenuButton label="Свежее" icon="calendar-icon"/>
    </div>
    <div class="d-flex flex-column block-menu">
      <div class="p1 text-color">Мои сообщества</div>
      <div v-for="group in filteredGroups" :key="group">
        <PrependMenuButton :label=group.name :icon=group.img />
      </div>
      <AppendIconButton 
        label="Больше сообществ"
        icon="arrow-next-icon"
        v-if="showMoreGroups"
      />
    </div>
    <div class="d-flex flex-column block-menu">
      <div class="p1 text-color">Полезная информация</div>
      <PrependMenuButton label="Правила" icon="rules-icon"/>
      <PrependMenuButton label="Заказать рекламу" icon="advertisement-icon"/>
    </div>
  </div>
</template>

<style scoped>
.left-menu {
  gap: 10px;
}
.block-menu {
  padding: 0px 20px;
  gap: 10px;
}
</style>

<script>
import PrependMenuButton from "@/components/basic/buttons/PrependMenuButton.vue";
import AppendIconButton from "@/components/basic/buttons/AppendIconButton.vue";

export default {
  name: "LeftMenuComponent",
  components: {
    PrependMenuButton,
    AppendIconButton,
  },
  props: {
    groups: {
      type: Array,
      default: () => [],
    }
  },
  data() {
    return {
      filteredGroups: [],
      showMoreGroups: false,
    };
  },
  mounted() {
    this.filterGroups(this.groups);
  },
  methods: {
    filterGroups(groups) {
      if (groups.length > 4) {
        this.filteredGroups = groups.slice(0, 4);
        this.showMoreGroups = true;
        return;
      }
      this.filteredGroups = groups;
    },
  },
};
</script>
