<template>

  <div :class="{'thumbnail-editor': edit}">
      <img
        class="upload-trigger"
        :src="thumbnailSrc"
        :alt="alt"
        :class="ratioClass"
      />

      <template v-if="edit">
        <!-- Upload mode -->
        <FileUploadModal
          v-if="uploading"
          :allowedMimetypes="allowedMimetypes"
          :endpoint="endpoint"
          @uploaded="onUpload"
          @started="$emit('uploadStarted')"
          @error="$emit('thumbnailError')"
          @cancelled="$emit('uploadCancelled')"
          @close="uploading = false"
        />

        <!-- Crop mode -->
      <div v-if="cropping" class="options-menu" :class="ratioClass">
        <a :title="$tr('cancel')" @click.stop="cancelCrop">
          not_interested
        </a>
        <a :title="$tr('submit')" @click.stop="submitCrop">
          check
        </a>
      </div>

      <!-- Options Menu -->
      <div v-else class="options-menu" :class="ratioClass">
        <!-- Always available -->
        <a :title="$tr('upload')" @click="uploading = true">
          image
        </a>

        <a v-if="thumbnailSet" :title="$tr('crop')" @click="cropping = true">
          crop
        </a>

        <a v-if="!isChannel" :title="$tr('generate')" @click="openThumbnailModal">
          camera
        </a>

        <a v-if="thumbnailSet" :title="$tr('remove')" @click="removeThumbnail">
          clear
        </a>
      </div>
    </template>
  </div>

</template>


<script>

import FileUploadModal from './FileUploadModal.vue';
import { FormatPresets } from 'edit_channel/constants/index';
import { Croppie } from 'croppie';
import _ from 'underscore';

export default {
  name: 'Thumbnail',
  $trs: {
    cancel: "Cancel",
    submit: "Submit",
    upload: "Upload",
    crop: "Recenter/Crop",
    generate: "Generate Thumbnail",
    remove: "Remove"
  },
  props: {
    // Toggles edit mode
    edit: {
      type: Boolean,
      default: false,
    },
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
      default: '',
      required: false,
    }
  },
  components: {
    FileUploadModal,
  },
  data() {
    return {
      cropping: false,
      uploading: false,
    }
  },
  computed: {
    thumbnailSet() {
      return Boolean(this.value);
    },
    // Ensures that we don't propogate changes up to component if we're just using default
    thumbnailSrc() {
      return this.thumbnailSet ? this.value : this.defaultUrl;
    },
    endpoint() {
      return window.Urls.thumbnail_upload();
    },
    allowedMimetypes() {
      // console.info('FormatPresets', FormatPresets);
      let kind = this.isChannel ? null : this.kindId;
      return _.findWhere(FormatPresets, {kind_id: kind, thumbnail: true}).associated_mimetypes;
    },
    ratioClass() {
      if (this.isChannel) {
        return 'square';
      }
      return '';
    },
    isChannel() {
      return this.kindId === "channel";
    }
  },
  methods: {
    cancelCrop(event) {
      event.stopImmediatePropagation()
      _.defer(() => {
        this.cropping = false;
      })
    },
    submitCrop() {
      console.info("SUBMITTING CROPPED IMAGE")
      this.cropping = false;
    },
    removeThumbnail() {
      this.$emit('input', null)
      this.$emit("removeThumbnail");
    },
    onUpload(data) {
      // Update parent's data (standard v-model functionality)
      this.$emit('input', data.path);

      // Prep data to be sent to vuex state, where the change will take place
      data.encoding = {'base64': data.encoding, 'points': [], 'zoom': 0};
      this.$emit('uploadedThumbnail', data);

      // Ideally, this component receives and emits all the data necessary for submission.
    }
  }
};

</script>


<style lang="less" scoped>

  @import '../../../../less/global-variables.less';
  @default-image-width: 170px;
  @default-image-height: 100px;
  @default-square-width: 130px;

  img {
    width: @default-image-width;
    height: @default-image-height;
    object-fit: cover;
    object-position: center;
    &.square {
      width: @default-square-width;
      height: @default-square-width;
    }
  }

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
    &.square {
      width: @default-square-width;
    }
    a {
      .material-icons;
      color: @gray-400;
      cursor: pointer;
      font-size: 15pt;
      text-decoration: none;
      &:hover{ color: white; }
    }
  }

</style>

require("images.less");
require("dropzone/dist/dropzone.css");
require("croppie/croppie.css");
var dialog = require("edit_channel/utils/dialog");
const State = require("edit_channel/state");
const Constants = require("edit_channel/constants/index");

const CHANNEL_ASPECT_RATIO = { width: 130,  height: 130 };
const CHANNEL_CROP_BOUNDARY = { width: CHANNEL_ASPECT_RATIO.width + 20,  height: CHANNEL_ASPECT_RATIO.height + 20 };
const THUMBNAIL_ASPECT_RATIO = { width: 160,  height: 90 };
const THUMBNAIL_CROP_BOUNDARY = { width: THUMBNAIL_ASPECT_RATIO.width + 10,  height: THUMBNAIL_ASPECT_RATIO.height + 10 };

var MESSAGES = {
    "upload": "Upload",
    "submit": "Submit",
    "use": "USE",
    "image_error": "Image Error",
    "file_error_text": "Error uploading file: connection interrupted",
    "unable_to_generate": "Unable to generate thumbnail for this item",
    "removing_image": "Removing Image",
    "removing_image_text": "Are you sure you want to remove this image?",
    "alt_prompt": "Enter text to display if image fails to load",
    "drop_prompt": "Click or drop file here...",
    "adding_image": "Adding image to exercise",
    "generate": "Generate",
    "generate_thumbnail_text": "Click 'Generate' to create a thumbnail",
    "recenter_thumbnail": "Recenter/Crop",
    "no_space": "Not enough space. Check your storage under Settings page.",
}
var ThumbnailUploadView = BaseViews.BaseView.extend({
    template: require("./hbtemplates/thumbnail_upload.handlebars"),
    preview_template: require("./hbtemplates/thumbnail_preview.handlebars"),
    dropzone_template: require("./hbtemplates/thumbnail_dropzone.handlebars"),
    name: NAMESPACE,
    $trs: MESSAGES,
    initialize: function(options) {
        _.bindAll(this, 'image_uploaded','image_added','image_removed','create_dropzone', 'image_completed','image_failed',
                         'use_image', 'create_croppie', 'cancel_croppie', 'submit_image', 'submit_croppie');
        this.image_url = options.image_url;
        this.image = _.find(this.model.get('files'), function(f){ return f.preset.thumbnail; });
        if(this.image){
            this.image = new Models.FileModel(this.image);
        }
        this.thumbnail_encoding = this.model.get('thumbnail_encoding');
        this.original_thumbnail_encoding = this.thumbnail_encoding;
        this.onsuccess = options.onsuccess;
        this.onremove = options.onremove;
        this.onerror = options.onerror;
        this.onfinish = options.onfinish;
        this.onstart = options.onstart;
        this.preset_id = options.preset_id;
        this.acceptedFiles = options.acceptedFiles;
        this.upload_url = options.upload_url;
        this.default_url = options.default_url;
        this.allow_edit = options.allow_edit;
        this.aspect_ratio = (options.is_channel)? CHANNEL_ASPECT_RATIO : THUMBNAIL_ASPECT_RATIO;
        this.boundary = (options.is_channel)? CHANNEL_CROP_BOUNDARY : THUMBNAIL_CROP_BOUNDARY;
        this.cropping = false;
        this.render();
        this.dropzone = null;
        this.image_success = true;
    },
    events: {
        'click .remove_image ' : 'remove_image',
        'click .open_thumbnail_generator': 'open_thumbnail_generator',
        'click .crop_image': 'create_croppie',
        'click .cancel_image': 'cancel_croppie',
        'click .submit_image': 'submit_croppie'
    },
    render: function() {
        var thumbnail_src = this.get_thumbnail_url();
        if(this.allow_edit){
            this.$el.html(this.template({
                picture : thumbnail_src,
                selector: this.get_selector(),
                show_generate: this.model.get('kind') != undefined,
                not_default: thumbnail_src != this.default_url,
                cropping: this.cropping,
            }, {
                data: this.get_intl_data()
            }));
            if(!this.cropping) {
                _.defer(this.create_dropzone, 1000);
            }
        }else{
            this.$el.html(this.preview_template({
                picture : thumbnail_src,
                name: this.model.get('title')
            }));
        }
    },

    /*********** GET IMAGE INFORMATION ***********/
    get_selector: function(){
        return "dropzone_image_" + this.cid;
    },
    get_thumbnail_url:function(ignore_encoding){
        var thumbnail = _.find(this.model.get('files'), function(f){ return f.preset.thumbnail; });
        if(!ignore_encoding && this.thumbnail_encoding && this.thumbnail_encoding.base64){
            return this.thumbnail_encoding.base64;
        }
        else if(this.image_url){ return this.image_url; }
        else if(thumbnail){ return thumbnail.storage_url; }
        else if(this.model.get('kind') != undefined) { return "/static/img/" + this.model.get("kind") + "_placeholder.png"; }
        else{ return "/static/img/kolibri_placeholder.png"; }
    },

    /*********** UPDATE IMAGE FIELDS ***********/
    remove_image: function(){
        var self = this;
        dialog.dialog(this.get_translation("removing_image"), this.get_translation("removing_image_text"), {
            [this.get_translation("cancel")]:function(){},
            [this.get_translation("remove")]: function(){
                self.image = null;
                self.image_url = self.default_url;
                self.thumbnail_encoding = {};
                self.onremove();
                self.render();
            },
        }, function(){});
    },
    submit_image:function(){
        this.original_thumbnail_encoding = this.thumbnail_encoding;
        if(this.onsuccess){ this.onsuccess(this.image, this.thumbnail_encoding, this.image_formatted_name, this.image_url); }
        if(this.onfinish){ this.onfinish(); }
    },

    /*********** CROPPIE FUNCTIONS ***********/
    create_croppie:function(){
        this.cropping = true;
        this.render();
        this.$(".finished_area").css("visibility", "visible");
        var selector = "#" + this.get_selector() + "_placeholder";
        var self = this;
        var thumbnail_src = this.get_thumbnail_url(true);
        $(selector).attr('src', thumbnail_src); // Need to set the src to be url or croppie
                                                // will zoom in on encoding and not allow
                                                // user to zoom out

        this.croppie = new Croppie(this.$(selector).get(0),{
            boundary: this.boundary,
            viewport: this.aspect_ratio,
            showZoomer: false,
            customClass: "crop-img"
        });

        // TODO: This should make thumbnails retain zoom/points when you re-enter cropping mode, but
        // it seems like there's a bug with croppie https://github.com/Foliotek/Croppie/issues/122
        // Uncomment these lines when it gets fixed
        // this.croppie.bind({
        //     points: (this.thumbnail_encoding)? this.thumbnail_encoding.points : [],
        //     zoom: (this.thumbnail_encoding)? this.thumbnail_encoding.zoom : 0,
        //     url: thumbnail_src
        // }).then(function(){});
    },
    cancel_croppie: function(){
        this.cropping = false;
        this.thumbnail_encoding = this.original_thumbnail_encoding;
        this.croppie.destroy();
        this.render();
    },
    submit_croppie: function(){
        this.cropping = false;
        var self = this;
        var result = this.croppie.get();
        this.croppie.result({type: 'base64', size: this.aspect_ratio}).then(function(image){
            self.thumbnail_encoding = {
                "points": result.points,
                "zoom": result.zoom,
                "base64": image
            };
            self.submit_image();
            self.render();
        });
    },

    /*********** GENERATE IMAGE FUNCTIONS ***********/
    open_thumbnail_generator:function(){
        var thumbnail_modal = new ThumbnailModalView({
            node: this.model,
            onuse: this.use_image,
            model: this.image
        });
    },
    use_image:function(file, encoding){
        this.image = file;
        this.image_url = file.get('storage_url');
        this.thumbnail_encoding = {'base64': encoding, 'points': [], 'zoom': 0};
        this.render();
        this.submit_image();
    },

    /*********** DROPZONE FUNCTIONS ***********/
    create_dropzone:function(){
        var selector = "#" + this.get_selector();
        Dropzone.autoDiscover = false;
        if(this.$(selector).is(":visible")){
            this.dropzone = new Dropzone(this.$(selector).get(0), {
                maxFiles: 1,
                clickable: [selector + "_placeholder", selector + "_swap"],
                acceptedFiles: this.acceptedFiles,
                url: this.upload_url,
                previewTemplate:this.dropzone_template(null, { data: this.get_intl_data() }),
                previewsContainer: selector,
                headers: {"X-CSRFToken": get_cookie("csrftoken"), "Preset": this.preset_id, "Node": this.model.id}
            });
            this.dropzone.on("success", this.image_uploaded);
            this.dropzone.on("addedfile", this.image_added);
            this.dropzone.on("removedfile", this.image_removed);
            this.dropzone.on("queuecomplete", this.image_completed);
            this.dropzone.on("error", this.image_failed);
        }
    },
    image_failed:function(data, error, xhr){
        this.image_error = (xhr && xhr.status === 403) ? this.get_translation("no_space") : error;
    },
    image_added:function(thumbnail){
        this.image_error = this.get_translation("file_error_text");
        this.$(".finished_area").css('display', 'none');
        this.$("#" + this.get_selector() + "_placeholder").css("display", "none");
        if(this.onstart){ this.onstart(); }
    },
    image_removed:function(thumbnail){
        this.image_error = null;
        this.$("#" + this.get_selector() + "_placeholder").css("display", "block");
        this.$(".finished_area").css('display', 'block');
        if(this.onfinish){ this.onfinish(); }
    },
    image_uploaded:function(image){
        this.image_error = null;
        var result = JSON.parse(image.xhr.response)
        if(result.file){
            this.image = new Models.FileModel(JSON.parse(result.file));
        }
        this.image_url = result.path;
        this.image_formatted_name = result.formatted_filename;
        this.encoding = result.encoding;
    },
    image_completed:function(){
        if(this.image_error){
            var self = this;
            dialog.alert(this.get_translation("image_error"), this.image_error);
            if(this.onerror){ this.onerror(); }
            this.render();
        } else{
            this.thumbnail_encoding = {'base64': this.encoding, 'points': [], 'zoom': 0};
            this.render();
            this.submit_image();
        }
    }
});
