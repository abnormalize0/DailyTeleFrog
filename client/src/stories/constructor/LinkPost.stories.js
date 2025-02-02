import LinkPost from "@/components/constructor/LinkPost.vue";

export default {
  component: LinkPost,
  title: 'LinkPost',
  tags: ['autodocs'],
  decorators: [() => ({
    template: '<div style="margin: 3em;"><story/></div>'
  })]
}

export const Default = {
  args: {
    preheader: 'Ответ на пост "А вот это интересная точка зрения"',
    text: 'Сама по себе религия - это хорошо. По идее во всех священных писаниях просто начертались условия выживания. Знаете зачем нужен вот этот сорокадневный пост? Да чтобы вы последнюю скотину',
    image: 'src/assets/img-placeholder.png',
  }
}