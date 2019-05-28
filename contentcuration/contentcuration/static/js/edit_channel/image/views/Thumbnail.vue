<template>

  <!-- Global styles applies style to .thumbnail -->
  <div class="thumbnail-component">
    <div class="thumbnail-wrap" :class="{'thumbnail-editor': edit, 'square': isChannel}">
      <img :src="thumbnailSrc" :alt="alt">

      <template v-if="edit">
        <!-- Upload mode -->
        <!-- Currently uploads immediately. Assigned to node by parent -->
        <FileUpload
          v-if="uploading"
          :allowedMimetypes="allowedMimetypes"
          :endpoint="endpoint"
          @upload="$emit('uploadStarted')"
          @upload-success="onUpload"
          @error="$emit('thumbnailError')"
          @cancelled="$emit('uploadCancelled')"
          @close="uploading = false"
        />

          <!-- Crop mode -->
        <div v-if="cropping" class="options-menu">
          <a :title="$tr('cancel')" @click.stop="cancelCrop">
            not_interested
          </a>
          <a :title="$tr('submit')" @click.stop="submitCrop">
            check
          </a>
        </div>

        <!-- Options Menu -->
        <div v-else class="options-menu">
          <!-- Always available -->
          <a :title="$tr('upload')" @click="uploading = true">
            image
          </a>

          <a v-if="thumbnailSet" :title="$tr('crop')" @click="cropping = true">
            crop
          </a>

          <a v-if="true" :title="$tr('generate')" @click="generateThumbnail">
            camera
          </a>

          <a v-if="thumbnailSet" :title="$tr('remove')" @click="removeThumbnail">
            clear
          </a>
        </div>
      </template>
    </div>

    <span v-if="error" class="thumbnail-error" role="alert">
      {{ error }}
    </span>
  </div>

</template>


<script>

import { Croppie } from 'croppie';
import _ from 'underscore';
import FileUpload from 'edit_channel/FileUpload/index.vue';
import { FormatPresets } from 'edit_channel/constants/index';

export default {
  name: 'Thumbnail',
  $trs: {
    cancel: 'Cancel',
    submit: 'Submit',
    upload: 'Upload',
    crop: 'Recenter/Crop',
    generate: 'Generate Thumbnail',
    remove: 'Remove',
    generationFailureMessage: 'Unable to generate thumbnail for this item',
  },
  props: {
    // Toggles edit mode
    edit: {
      type: Boolean,
      default: false,
    },
    // TODO rename prop
    // URL for thumbnail to be displayed
    value: {
      type: String,
      required: false,
    },
    // Define default URL if it doesn't exist
    defaultUrl: {
      type: String,
      default: '/static/img/kolibri_placeholder.png',
      required: false,
    },
    // Used to determine settings based on the node being displayed
    kindId: {
      type: String,
      required: true,
    },
    // Alt text for this image
    alt: {
      type: String,
      default: ``,
      required: false,
    },
    // Only ever used to make thumbnail generation request
    contentNodeId: {
      type: String,
      default: ``,
      required: false,
    },
  },
  components: {
    FileUpload,
  },
  data() {
    return {
      cropping: false,
      uploading: false,
      error: '',
    }
  },
  computed: {
    thumbnailSet() {
      return Boolean(this.value);
    },
    // Ensures that we don't propogate changes up to component if we're just using default
    thumbnailSrc() {
      return this.value || this.defaultUrl;
    },
    endpoint() {
      return window.Urls.thumbnail_upload();
    },
    allowedMimetypes() {
      // console.info('FormatPresets', FormatPresets);
      const kind = this.isChannel ? null : this.kindId;
      const associatedPreset = FormatPresets.find(preset =>
        preset.kind_id === kind && preset.thumbnail
      );
      return associatedPreset.associated_mimetypes;
    },
    isChannel() {
      return this.kindId === "channel";
    }
  },
  methods: {
    cancelCrop(event) {
      this.cropping = false;
    },
    submitCrop() {
      console.info("SUBMITTING CROPPED IMAGE")
      this.cropping = false;
    },
    removeThumbnail() {
      this.$emit('input', null)
      this.$emit('removeThumbnail');
    },
    onUpload(file, request) {
      // Update parent's data (standard v-model functionality)
      this.$emit('input', request.body.path);

      // Prep data to be sent to vuex state, where the change will take place
      this.$emit('uploadedThumbnail', Object.assign({}, request.body, {
        encoding: {
          'base64': request.body.encoding,
          'points': [],
          'zoom': 0},
        }
      ));

      // Ideally, this component receives and emits all the data necessary for submission.
    },
    generateThumbnail() {
      console.log('Thumbnail generation requested');
      $.ajax({
        method: 'POST',
        url: window.Urls.generate_thumbnail(this.contentNodeId),
        success: result => {
          const response = JSON.parse(result)
          this.$emit('uploadedThumbnail', response);
          this.$emit('input', response.path);
        },
        error: error => {
            this.error = this.$tr('generationFailureMessage');
            this.$emit('thumbnailError', error);
        },
      });
    },
  }
};

</script>


<style lang="less" scoped>

  @import '../../../../less/global-variables.less';
  @default-image-width: 170px;
  @default-image-height: 100px;
  @default-square-width: 130px;

  // Dimensions
  .thumbnail-wrap {
    height: @default-image-height;
    width: @default-image-width;
    &.square{
      height: @default-square-width;
      width: @default-square-width;
    }
  }

  img {
    object-fit: cover;
    object-position: center;
    width: 100%;
    height: 100%;
  }

  // Edit mode
  .thumbnail-editor {
    img {
      cursor: pointer;
      border: 4px dashed @gray-400;
      opacity: 0.8;
    }

    &:hover .options-menu {
      visibility: visible;
    }
  }


  .options-menu {
    visibility: hidden;
    display: grid;
    grid-auto-flow: column;
    justify-content: space-around;
    background-color: rgba(0,0,0,0.7);
    padding: 5px 10px;
    margin-top: -30px;
    position: relative;
    a {
      .material-icons;
      color: @gray-400;
      cursor: pointer;
      font-size: 15pt;
      text-decoration: none;
      &:hover{ color: white; }
    }
  }

  .thumbnail-error {
    color: red;
  }

</style>
