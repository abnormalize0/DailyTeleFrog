import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue"


export default {
  component: BasicSecondaryButton,
  title: 'BasicSecondaryButton',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em; width: 79px;"><story/></div>'
  })]
}

export const Default = {
  args: {
    content: 'ВОЙТИ'
  }
}