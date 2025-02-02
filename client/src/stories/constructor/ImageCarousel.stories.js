import ImageCarousel from "@/components/constructor/ImageCarousel.vue";
import {sleep} from "@/utils/utils";
import { userEvent, within } from "@storybook/test";

export default {
  component: ImageCarousel,
  title: 'ImageCarousel',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

export const Default = {
  args: {
    imgs: ['src/assets/img-placeholder-carousel.png']
  }
}

export const Multiple = {
  args: {
    imgs: [
      'src/assets/img-placeholder-carousel.png',
      'src/assets/img-placeholder-carousel.png'
    ]
  }
}

Multiple.play = async ({canvasElement}) => {
  await sleep(2000);
  const canvas = within(canvasElement);
  const radio = canvas.getAllByRole("radio");
  await userEvent.click(radio[1]);
  await sleep(2000);
  await userEvent.click(radio[0]);
  await sleep(2000);
}