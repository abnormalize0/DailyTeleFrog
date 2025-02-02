import DefaultLink from "@/components/constructor/DefaultLink.vue";

export default {
  component: DefaultLink,
  title: 'DefaultLink',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}


export const Default = {
  args: {
    image: 'src/assets/img-placeholder-default-link.png',
    linkText: 'rebellion.com',
    header: 'Were not gonna take it!',
    text: 'A lot of text about this ridiculous rebelliion and a'
  }
}