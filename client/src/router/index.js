import { createRouter, createWebHistory } from 'vue-router'
import FeedView from '../views/FeedView.vue'
import NewPostView from '../views/NewPostView.vue'
import PostView from '../views/PostView.vue'
import TagView from '../views/TagView.vue'
import ProfileView from '../views/ProfileView.vue'

const routes = [
  {
    path: '/',
    name: 'feed',
    component: FeedView,
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView
  },
  {
    path: '/new_post',
    name: 'new_post',
    component: NewPostView
  },
  {
    path: '/post/:id',
    name: 'post',
    component: PostView
  },
  {
    path: '/tag/:id',
    name: 'tag',
    component: TagView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
