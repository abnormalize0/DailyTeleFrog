import { createRouter, createWebHistory } from 'vue-router'
import FeedView from '../views/FeedView.vue'
import AboutView from '../views/AboutView.vue'
import ExitView from '../views/ExitView.vue'
import RegisterView from '../views/RegisterView.vue'
import LoginView from '../views/LoginView.vue'
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
    path: '/about',
    name: 'about',
    component: AboutView
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView
  },
  {
    path: '/exit',
    name: 'exit',
    component: ExitView
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
