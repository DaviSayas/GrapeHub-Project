// GrapeHub — application entry point.
const { createApp } = Vue;
import router from './router/index.js';

const App = {
  name: 'GrapeHub',
  template: `<router-view></router-view>`,
};

createApp(App).use(router).mount('#app');
