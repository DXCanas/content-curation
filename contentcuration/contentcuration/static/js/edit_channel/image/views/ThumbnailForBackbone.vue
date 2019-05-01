<template>

  <!--
    Have to bind each event individually rather than using `v-bind`
    because listeners added with`vm.$on` aren't included in $listeners
  -->
  <Thumbnail
    v-bind="props"
    @input="$emit('input', $event)"
    @uploadedThumbnail="$emit('uploadedThumbnail', $event)"
    @removeThumbnail="$emit('removeThumbnail', $event)"
    @thumbnailError="$emit('thumbnailError', $event)"
    @uploadStarted="$emit('uploadStarted', $event)"
    v-model="props.value"
    v-on="$listeners"
  />

</template>


<script>

  import Thumbnail from './Thumbnail.vue';

  export default {
    name: 'ThumbnailForBackbone',
    components: {
      Thumbnail,
    },
    data() {
      return {
        props,
      }
    },
  };

</script>


<style lang="scss" scoped></style>
