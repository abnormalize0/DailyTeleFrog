import HeadingLevel2 from "@/components/constructor/HeadingLevel2.vue";

export default {
  component: HeadingLevel2,
  title: 'HeadingLevel2',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

export const Default = {
  args: {
    content: 'Заголовок второго уровня'
  }
}