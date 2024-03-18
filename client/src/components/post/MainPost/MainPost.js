
import PostFooter from "../PostFooter/PostFooter.vue";
export default {
  name: 'MainPost',
  components: {
    PostFooter
  },
  props: {
    header: String,
    body: String,
    img: String,
    hashtags: Array,
    avatarImg: String,
    profileName: String,
    accountTag: String
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

