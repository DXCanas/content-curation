import Vue from 'vue';
import ThumbnailForBackbone from './ThumbnailForBackbone.vue';

export default function(options, props) {
  // Needs to be wrapped to pass data into props and have it be reactive
  const wrappedComponent = Object.assign(ThumbnailForBackbone, {
    data() {
      return {
        props,
      };
    },
  });
  const instantiatedComponent = Vue.extend(wrappedComponent)
  return new instantiatedComponent(options);
}
