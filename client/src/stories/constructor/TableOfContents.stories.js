import TableOfContents from "@/components/constructor/TableOfContents.vue";

export default {
  component: TableOfContents,
  title: 'TableOfContents',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

const links = [
  {
    key: 'Текст параграфа 1',
    links: [
      {
        key: 'Текст параграфа 2',
        links: [
          {
            key: 'Текст параграфа 3'
          }
        ]
      }
    ]
  },
  {
    key: 'Текст парграфа 4'
  }
];

export const Default = {
  args: {
    links: links,
  }
}