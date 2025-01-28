import ImageCarousel from "@/components/constructor/ImageCarousel.vue";

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