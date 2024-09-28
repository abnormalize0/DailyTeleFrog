import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import LoggedInComponent from "@/components/common/profile/LoggedInComponent.vue";
import ProfileComponent from "@/components/common/profile/ProfileComponent.vue";

export default {
  components: {LoggedInComponent, BasicPrimaryButton, ProfileComponent},
  title: 'LoggedInComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}
const Template = (args) => ({
  components: {BasicPrimaryButton, LoggedInComponent, ProfileComponent},
  setup() {
    return args;
  },
  template: '<LoggedInComponent />',
})

export const Default = Template.bind({})
