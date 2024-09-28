import AppendIconButton from "@/components/basic/buttons/AppendIconButton.vue";

export default {
  component: AppendIconButton,
  title: 'AppendIconButton',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em; width: 123px;"><story/></div>'
  })]
}

export const Default = {
  args: {
    label: 'БОЛЬШЕ СООБЩЕСТВ',
    icon: 'arrow-next-icon'
  }
}
