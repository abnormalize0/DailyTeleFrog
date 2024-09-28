import BasicPrimaryButton from "@/components/basic/buttons/BasicPrimaryButton.vue";
import BasicSecondaryButton from "@/components/basic/buttons/BasicSecondaryButton.vue";
import BasicInput from "@/components/basic/input/BasicInput.vue";
import ProfileComponent from "@/components/common/profile/ProfileComponent.vue";
import RegistrationComponent from "@/components/common/profile/RegistrationComponent.vue";

export default {
  components: {RegistrationComponent, BasicPrimaryButton, BasicInput, BasicSecondaryButton, ProfileComponent},
  title: 'RegistrationComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

const Template = (args) => ({
  components: {RegistrationComponent, BasicPrimaryButton, BasicInput, BasicSecondaryButton, ProfileComponent},
  setup() {
    return args;
  },
  template: '<RegistrationComponent />',
})

export const Default = Template.bind({});