import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";

export default {
  component: BasicPrimaryButton,
  title: 'BasicPrimaryButton',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em; width: 79px;"><story/></div>'
  })]
}

export const Default = {
  args: {
    content: 'ВОЙТИ',
    disabled: false
  }
}

export const Disabled = {
  args: {
    content: 'ВОЙТИ',
    disabled: true,
  },
}