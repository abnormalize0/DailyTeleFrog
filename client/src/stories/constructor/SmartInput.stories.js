import SmartInput from "@/components/feed/post-creation/SmartInput.vue";

export default {
    component: SmartInput,
    title: 'SmartInput',
    tags: ['autodocs'],
    decorators: [() => ({
      template: '<div style="margin: 3em;"><story/></div>'
    })]
}

const FocusedTemplate = (args) => ({
    components: {BasicInput},
    setup() {
      return args;
    },
    mounted() {
      this.$refs.inputElement.$el.querySelector('input-search').focus();
    },
    template: `<SmartInput ref="inputElement"/>`
});
  
export const Default = {
    args: {
        label: 'Напишите что-то, или введите “/” для команд...'
    }
}
export const Focused = FocusedTemplate.bind({});