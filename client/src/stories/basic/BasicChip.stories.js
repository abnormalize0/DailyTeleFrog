import BasicChip from "@/components/basic/BasicChip.vue"

export default {
  component: BasicChip,
  title: 'BasicChip',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

export const Default = {
  args: {
    content: 'Игры',
  }
}