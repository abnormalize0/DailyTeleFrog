import BasicInput from "@/components/basic/input/BasicInput.vue"

export default {
  component: BasicInput,
  title: 'BasicInput',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em; width: 143px;"><story/></div>'
  })]
}

const FocusedTemplate = (args) => ({
  components: {BasicInput},
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.$el.querySelector('input').focus();
  },
  template: `<BasicInput ref="inputElement" label="Email"/>`
});

const PopulateTemplate = (args) => ({
  components: {BasicInput},
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.modelValue = "test";
    this.$refs.inputElement.$el.querySelector('input').focus();
  },
  template: `<BasicInput ref="inputElement" label="Email" />`
});

const FilledTemplate = (args) => ({
  components: { BasicInput },
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.modelValue = "test@gmail.com";
  },
  template: `<BasicInput ref="inputElement" label="Email" />`
});

const ErrorTemplate = (args) => ({
  components: { BasicInput },
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.modelValue = "test@";
    this.$refs.inputElement.errorVisible = true;
    this.$refs.inputElement.errorMessage = 'Email некорректный';
  },
  template: `<BasicInput ref="inputElement" label="Email" />`
});

const PasswordFilledTemplate = (args) => ({
  components: { BasicInput },
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.modelValue = "testPass";
  },
  template: `<BasicInput ref="inputElement" type="password" label="Пароль"/>`
});
const PasswordFocusedTemplate = (args) => ({
  components: { BasicInput },
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.modelValue = "testPass";
    this.$refs.inputElement.$el.querySelector('input').focus();
  },
  template: `<BasicInput ref="inputElement" type="password" label="Пароль"/>`
});
const PasswordSwapTemplate = (args) => ({
  components: { BasicInput },
  setup() {
    return args;
  },
  mounted() {
    this.$refs.inputElement.modelValue = "testPass";
    this.$refs.inputElement.passwordVisible = true;
    this.$refs.inputElement.$el.querySelector('input').focus();
  },
  template: `<BasicInput ref="inputElement" type="password" label="Пароль"/>`
})


export const Default = {
  args: {
    label: 'E-mail'
  }
}
export const Focused = FocusedTemplate.bind({});
export const Populate = PopulateTemplate.bind({});
export const Filled = FilledTemplate.bind({});
export const Error = ErrorTemplate.bind({});
export const Password = {
  args: {
    label: 'Пароль',
    type: 'password'
  }
}
export const PasswordFilled = PasswordFilledTemplate.bind({});
export const PasswordFocused = PasswordFocusedTemplate.bind({});
export const PasswordSwap = PasswordSwapTemplate.bind({});