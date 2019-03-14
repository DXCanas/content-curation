<template>

  <!-- Container that Uppy's Dashboard will populate -->
  <div ref="dashboardTarget"></div>

</template>


<script>

// Essentially tightly integrated Vue wrapper for Uppy's Dashboard.
// Includes all of our Plugins & Definitions

// Should be a clean, tree-shaken import
import {
  Core as Uppy,
  XHRUpload,
  Dashboard,
  GoogleDrive,
  Dropbox,
  URL,
} from 'uppy';

// Might be a good place to try async imports
// import Uppy from '@uppy/core';
// import XHRUpload from '@uppy/xhr-upload';
// import Dashboard from '@uppy/dashboard';
// import GoogleDrive from '@uppy/google-drive';
// import Dropbox from '@uppy/dropbox';
// import Url from '@uppy/url';

import {
  FormatPresets
} from 'edit_channel/constants/index';

import get_cookie from 'utils/get_cookie';
import { alert } from 'edit_channel/utils/dialog.js';
import _ from 'underscore';

// import ProgressBar from '@uppy/progress-bar';
// import Retriever from '@uppy/golden-retriever';

require('@uppy/core/dist/style.css')
require('@uppy/dashboard/dist/style.css')

export default {
  name: 'ThumbnailUploadModal',
  $trs: {
    enterUrlToImport: 'Enter URL to import a file',
    import: 'Import',
    failedToFetch: 'Companion failed to fetch this URL, please make sure it’s correct',
    enterCorrectUrl: 'Incorrect URL: Please make sure you are entering a direct link to a file',
    closeModal: 'Close',
    dashboardTitle: 'Uploading File(s)',
    dashboardWindowTitle: 'Uploading File(s) (Press escape to close)',
    cancel: "Cancel",
    dropPaste: "Drop files here, paste, or import from",
    myDevice: "My Device",
    link: "Link",
    addMoreFiles: "Add more files",
    removeFile: "Remove file",
    uploadComplete: "Upload Complete",
    retryUpload: "Retry upload",
    resumeUpload: "Resume upload",
    pauseUpload: "Pause upload",
    uploadError: "Upload Error"
  },
  props: {
    windowTitle: {
      type: String,
      required: false,
      default: this.$tr('dashboardWindowTitle')
    },
    title: {
      type: String,
      required: false,
      default: this.$tr('DashboardTitle')
    },
    allowedMimetypes: {
      type: Array,
      required: false,
      default() {
        return _.chain(FormatPresets)
                .where({supplementary: false})
                .pluck('associated_mimetypes')
                .flatten().uniq().value();
      },
    },
    multiple: {
      type: Boolean,
      default: false
    },
    endpoint: {
      type: String,
      default: window.Urls.file_create()
    },
  },
  computed: {
    dashboardOptions() {
      // Used in a hook within Dashboard
      const vueInstance = this;

      return {
        // Dashboard complains about lack of trigger.
        // We don't need it, as well call open manually.
        trigger: null,
        // inline: this.inline,
        // closeAfterFinish: !this.inline,
        target: this.$refs.dashboardTarget,
        replaceTargetContent: true,
        showProgressDetails: true,
        // showLinkToFileUploadResult: false,
        proudlyDisplayPoweredByUppy: false,
        closeModalOnClickOutside: true,
        onRequestCloseModal() {
          vueInstance.closeModal();
        },
        locale: {
          strings: {
            dashboardTitle: this.title,
            dashboardWindowTitle: this.windowTitle,
            closeModal: this.$tr('closeModal'),
            done: this.$tr('cancel'),
            dropPaste: this.$tr('dropPaste'),
            dropPasteImport: this.$tr('dropPaste'),
            myDevice: this.$tr('myDevice'),
            addMoreFiles: this.$tr('addMoreFiles'),
            removeFile: this.$tr('removeFile'),
            uploadComplete: this.$tr('uploadComplete'),
            retryUpload: this.$tr('retryUpload'),
            cancelUpload: this.$tr('cancel'),
            resumeUpload: this.$tr('resumeUpload'),
            pauseUpload: this.$tr('pauseUpload')
          }
        },
      };
    },
    serverUrl() {
      return "http://localhost:3020";
    },
    clientUrl() {
      return window.location.protocol + "//" + window.location.hostname + ":8080" + this.endpoint;
    },
    uppyOptions() {
      return {
        autoProceed: true,
        debug: window.DEBUG, // set by django
        restrictions: {
          // TODO make these definable
          // maxFileSize: false,
          allowedFileTypes: this.allowedMimetypes,
          maxNumberOfFiles: this.multiple ? null : 1
        },
        meta: {
          // Acts as more of a template. Will probably need preset
          // csrf: get_cookie('csrftoken'),
        },
      };
    },
    xhrUploadOptions() {
      return {
        endpoint: this.clientUrl,
        // formData: false,
        // bundle: false,
        headers: {
          'X-CSRFToken': get_cookie('csrftoken'),
          // 'Authorization': "Token " + "13a002460ce0e3aee2faa17e57e80cd41d3ce38a",
          // 'Authorization': get_cookie('csrftoken')
        },
        // rely on uppy's error event for errors
        // getResponseError: (responseText, xhr) => {
          // console.error(this.$tr("uploadError"), responseText, xhr);
          // alert(this.$tr("uploadError"), responseText);
          // this.closeModal();
          // return new Error(responseText)
        // }
      };
    },
    urlUploadOptions() {
      return {
        target: Dashboard,
        serverUrl: this.serverUrl,
        title: this.$tr('link'),
        locale: {
          strings: {
            import: this.$tr('import'),
            enterUrlToImport: this.$tr('enterUrlToImport'),
            failedToFetch: this.$tr('failedToFetch'),
            enterCorrectUrl: this.$tr('enterCorrectUrl')
          }
        }
      };
    },
    gDriveUploadOptions() {
      return {
        target: Dashboard,
        serverUrl: this.serverUrl
      };
    },
    dropboxUploadOptions() {
      return {
        target: Dashboard,
        serverUrl: this.serverUrl
      };
    },
  },
  created() {
    this.uppy = Uppy( this.uppyOptions )
    // Bind all events

    // Upload queue
    .on('file-added', file => this.$emit('fileAdded', file))
    .on('file-removed', this.onCancel)

    // Per-file
    // Response depends on upload mechanism
    .on('upload-success', reponse => this.$emit('uploadSuccess', reponse))
    .on('upload-error', reponse => this.$emit('uploadError', reponse))

    // Entire job
    .on('complete', result => this.$emit('complete', result))
    .on('error', result => this.$emit('error', result))
    // {
    //   console.log(result.failed, result.uploadID);
    //   console.log(JSON.stringify(result.successful[0]))
    // })


    // TODO test servers before adding plugins?
    this.uppy.use(XHRUpload, this.xhrUploadOptions);
  },
  mounted() {
    // Using mounted hook because dashboard requires certain DOM elements to be present

    // console.log("CSRF", get_cookie('csrftoken'));
    this.uppy.use(Dashboard, this.dashboardOptions)
    .use(URL, this.urlUploadOptions)
    .use(GoogleDrive, this.gDriveUploadOptions)
    .use(Dropbox, this.dropboxUploadOptions)

    this.uppy.getPlugin('Dashboard').openModal();
  },
  methods: {
    registerUppyPlugin(){
      // TODO registers plugin after testing for functionality
    },
  }
};

</script>


<style lang="less">
@import '../../../../less/global-variables.less';

// Need to use !important a lot because uppy's stylesheet
// has a lot of rules marked as !important :(
.uppy-Dashboard-inner {
  .uppy-DashboardContent-title {
    display: none;
  }
  .uppy-Dashboard-close {
    right: 10px !important;
    color: @gray-500 !important;
    top: 0px !important;
  }
  .uppy-DashboardTabs {
    .uppy-DashboardTab {
      .uppy-DashboardTab-btn {
        width: auto !important;
        padding: 5px 15px !important;
        margin: 0px 10px !important;
        svg {
          width: 50px !important;
          height: 50px !important;
        }
        .uppy-DashboardTab-name {
          font-family: @font-family !important;
          font-weight: bold !important;
          font-size: 12pt !important;
        }
        &:hover .uppy-DashboardTab-name {
          color: @blue-500 !important;
        }
      }
    }

    .uppy-Dashboard-dropFilesTitle {
      max-width: 100% !important;
      font-family: @font-family !important;
    }
  }
}

.uppy-Url {
  .uppy-c-textInput {
    .input-form !important;
    font-family: @font-family !important;
    outline: none !important;
    border-bottom-width: 2px !important;
    border-radius: 0px !important;
    margin-right: 10px;
    &:hover {
      border-color: @blue-500;
    }
  }
  .uppy-Url-importButton {
    .action-button !important;
    font-family: @font-family !important;
    text-transform: uppercase !important;
  }
}

.uppy-DashboardContent-bar {
  .uppy-DashboardContent-back {
    .action-text !important;
    font-family: @font-family !important;
    text-transform: uppercase !important;
  }
}

.uppy-Provider-auth {
  .uppy-Provider-authTitle {
    max-width: 100% !important;
    font-family: @font-family !important;
  }
  .uppy-Provider-authBtn {
    .action-button !important;
    font-weight: bold !important;
    font-family: @font-family !important;
  }
}

.uppy-ProviderBrowser-footer {
  .uppy-c-btn-primary {
    .action-button !important;
    text-transform: uppercase !important;
    font-family: @font-family !important;
  }
  .uppy-c-btn-link {
    .action-text !important;
    text-transform: uppercase !important;
    font-family: @font-family !important;
  }
}

</style>
