import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import ForgotPasswordComponent from "@/components/common/profile/ForgotPasswordComponent.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import ProfileComponent from "@/components/common/profile/ProfileComponent.vue";

export default {
  components: {BasicPrimaryButton, BasicSecondaryButton, BasicInput, ForgotPasswordComponent, ProfileComponent},
  title: 'ForgotPasswordComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

const Template = (args) => ({
  components: {BasicPrimaryButton, BasicSecondaryButton, BasicInput, ForgotPasswordComponent},
  setup() {
    return args;
  },
  template: '<ForgotPasswordComponent />',
})

export const Default = Template.bind({});