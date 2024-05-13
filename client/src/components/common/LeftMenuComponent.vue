<template>
  <div class="parent">
    <div class="child pointer">
      <i class="home-icon"></i>
      <div class="p2 menu-text">Моя лента</div>
    </div>
    <div class="child pointer">
      <i class="popular-icon"></i>
      <div class="p2 menu-text">Популярное</div>
    </div>
    <div class="child pointer">
      <i class="calendar-icon"></i>
      <div class="p2 menu-text">Свежее</div>
    </div>
    <div>
      <div class="p1" style="margin-bottom: 24px">Мои сообщества</div>
      <div v-for="group in filteredGroups" :key="group" class="child pointer">
        <img class="img" :src="group.img" />
        <div class="p2 menu-text">{{ group.name }}</div>
      </div>
      <div
        class="p3 pointer"
        style="
          margin-bottom: 24px;
          display: flex;
          justify-content: space-between;
        "
        v-if="showMoreGroups"
      >
        БОЛЬШЕ СООБЩЕСТВ
        <div style="margin-right: 4rem">></div>
      </div>
    </div>
    <div>
      <div class="p1" style="margin-bottom: 24px">Полезная информация</div>
      <div class="child pointer">
        <i class="rules-icon"></i>
        <div class="p2 menu-text">Правила</div>
      </div>
      <div class="child pointer">
        <i class="advertisement-icon"></i>
        <div class="p2 menu-text">Заказать рекламу</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.parent {
  padding: 15px 26px 10px 26px;
  color: white;
  width: 20rem;
}
.child {
  display: flex;
  justify-content: left;
  align-items: center;
  margin-bottom: 24px;
}
.pointer {
  cursor: pointer;
}
.menu-text {
  padding-left: 8px;
}
.img {
  width: 24px;
}
</style>

<script>
export default {
  name: "LeftMenuComponent",
  components: {
    
  },
  props: {
    groups: []
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
