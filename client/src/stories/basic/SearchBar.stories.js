import SearchBar from "@/components/basic/SearchBar.vue"

export default {
  component: SearchBar,
  title: 'SearchBar',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

const FocusedTemplate = (args) => ({
  components: {SearchBar},
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.$el.querySelector('input').focus();
  },
  template: `<SearchBar ref="inputElement"/>`
});

export const Default = {}
export const Focused = FocusedTemplate.bind({});