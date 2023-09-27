#!/bin/bash
rm -rf demo_project
vue create demo_project -p ./preset
cp -t demo_project/src/ App.vue main.js
cp router/* demo_project/src/router 
cp views/* demo_project/src/views 
cd demo_project
npm install @vueuse/core