import App from "@/App.vue";
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import SearchBar from "@/components/basic/SearchBar.vue";
import HeaderComponent from "@/components/common/HeaderComponent.vue";

export default {
  components: {HeaderComponent, BasicPrimaryButton, SearchBar, App},
  title: 'HeaderComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em; width: 1440px;"><story/></div>'
  })]
}

const Template = (args) => ({
  components: {HeaderComponent, BasicPrimaryButton, SearchBar, App},
  setup() {
    return args;
  },
  template: '<v-app class="background-main-color"><HeaderComponent /></v-app>',
})

export const Default = Template.bind({});