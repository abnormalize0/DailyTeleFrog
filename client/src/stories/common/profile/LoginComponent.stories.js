import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import LoginComponent from "@/components/common/profile/LoginComponent.vue";
import ProfileComponent from "@/components/common/profile/ProfileComponent.vue";

export default {
  components: {LoginComponent, BasicPrimaryButton, BasicSecondaryButton, BasicInput, ProfileComponent},
  title: 'LoginComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}
const Template = (args) => ({
  components: {LoginComponent, BasicPrimaryButton, BasicSecondaryButton, BasicInput},
  setup() {
    return args;
  },
  template: '<LoginComponent />',
})

export const Default = Template.bind({})
