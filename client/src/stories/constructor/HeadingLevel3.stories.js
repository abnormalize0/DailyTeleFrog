import HeadingLevel3 from "@/components/constructor/HeadingLevel3.vue";

export default {
  component: HeadingLevel3,
  title: 'HeadingLevel3',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

export const Default = {
  args: {
    content: 'Заголовок третьего уровня'
  }
}