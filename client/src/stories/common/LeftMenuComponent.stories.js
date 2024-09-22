import App from "@/App.vue";
import AppendIconButton from "@/components/basic/buttons/AppendIconButton.vue";
import PrependMenuButton from "@/components/basic/buttons/PrependMenuButton.vue";
import LeftMenuComponent from "@/components/common/LeftMenuComponent.vue";

export default {
  components: {LeftMenuComponent, PrependMenuButton, AppendIconButton, App},
  title: 'LeftMenuComponent',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em; width: 267px;"><story/></div>'
  })]
}

const Template = (args) => ({
  components: {LeftMenuComponent, PrependMenuButton, AppendIconButton, App},
  setup() {
    return args;
  },
  template: `
    <v-app class="background-main-color" style="padding-top: 1em;">
      <LeftMenuComponent :groups="[
        {name: 'onanisti', img: 'community-icon',},
        {name: 'dungeonSlaveZ', img: 'community-icon'}, 
        {name: 'boyNextDoor', img: 'community-icon'},
        {name: 'Jhohan pohan', img: 'community-icon'},
        {name: 'tester mokaka', img: 'community-icon'}
      ]"/>
    </v-app>
  `,
})

export const Default = Template.bind({});