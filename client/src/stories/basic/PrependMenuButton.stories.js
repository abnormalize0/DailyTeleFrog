import PrependMenuButton from "@/components/basic/buttons/PrependMenuButton.vue"

export default {
  component: PrependMenuButton,
  title: 'PrependMenuButton',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em; width: 143px;"><story/></div>'
  })]
}

export const Default = {
  args: {
    label: 'Моя лента',
    icon: 'home-icon'
  }
}