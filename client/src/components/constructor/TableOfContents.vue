<template>
  <div 
    class="p2 text-color"
  >
    <div v-for="header1 in links">
      {{ header1.key }}
      <div v-for="header2 in header1.links" 
        :style="'padding-left: 20px'">
        {{ header2.key }}
        <div v-for="header3 in header2.links"
          :style="'padding-left: 20px'">
          {{ header3.key }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "TableOfContents",
  props: {
    links: {
      type: Array, 
      default: () => ([])
    }
  },
}
</script>