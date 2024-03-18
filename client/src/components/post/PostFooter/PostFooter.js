
import PostHashtag from "../PostHashtag/PostHashtag.vue";
import AvatarSection from "../AvatarSection/AvatarSection.vue";
export default {
  name: 'post-footer',
  components: {
    PostHashtag,
    AvatarSection
  },
  props: {
    hashtags: Array,
    avatarImgSrc: String,
    profileName: String,
    profileTag: String
  },
  data () {
    return {

    }
  },
  computed: {

  },
  mounted () {

  },
  methods: {

  }
}


