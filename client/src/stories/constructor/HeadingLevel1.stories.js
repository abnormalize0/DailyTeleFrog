import HeadingLevel1 from "@/components/constructor/HeadingLevel1.vue";

export default {
  component: HeadingLevel1,
  title: 'HeadingLevel1',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

export const Default = {
  args: {
    content: 'Заголовок первого уровня'
  }
}