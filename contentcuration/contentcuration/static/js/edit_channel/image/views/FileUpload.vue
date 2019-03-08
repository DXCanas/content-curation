<template>

  <div>
    <div ref="container"></div>
  </div>

</template>


<script>

import Uppy from '@uppy/core';
import XHRUpload from '@uppy/xhr-upload';
import Dashboard from '@uppy/dashboard';
import GoogleDrive from '@uppy/google-drive';
import Url from '@uppy/url';
import Constants from 'edit_channel/constants/index';
import get_cookie from 'utils/get_cookie';
import { alert } from 'edit_channel/utils/dialog';

// import ProgressBar from '@uppy/progress-bar';
// import Retriever from '@uppy/golden-retriever';

require('@uppy/core/dist/style.css')
require('@uppy/dashboard/dist/style.css')

export default {
  name: 'FileUpload',
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
    presetId: {
      type: String,
      required: true
    },
    params: {
      type: Object,
      required: false,
      default() {
        return {};
      }
    },
    multiple: {
      type: Boolean,
      default: false
    },
    endpoint: {
      type: String,
      default: window.Urls.file_create()
    },
    trigger: {
      type: String,
      required: false
    },
    inline: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    allowedMimetypes() {
      if(this.presetId) {
        let preset = _.findWhere(Constants.FormatPresets, {id: this.presetId});
        return preset.associated_mimetypes;
      }
      return _.chain(Constants.FormatPresets)
              .where({supplementary: false})
              .pluck('associated_mimetypes')
              .flatten().uniq().value();
    }
  },
  data() {
    return {
      uppy: null
    }
  },
  mounted() {
    this.load();
  },
  methods: {
    openModal() {
      const dashboard = this.uppy.getPlugin('Dashboard');
      if(this.uppy && !this.inline && !dashboard.isModalOpen()) {
        dashboard.openModal();
      }
    },
    closeModal() {
      const dashboard = this.uppy.getPlugin('Dashboard');
      if(this.uppy && !this.inline && dashboard.isModalOpen()) {
        dashboard.closeModal();
      }
    },
    load() {
      this.uppy = Uppy({
        autoProceed: true,
        debug: false, //window.DEBUG,
        restrictions: {
          maxFileSize: false,
          allowedFileTypes: this.allowedMimetypes,
          maxNumberOfFiles: this.multiple? null : 1
        },
        meta: {
          preset: this.presetId,
          ...this.params
        },
        // onBeforeFileAdded: (currentFile, files) => Promise.resolve(),
        // onBeforeUpload: (files, done) => Promise.resolve(),
      })
      .use(XHRUpload, {
        endpoint: this.endpoint,
        headers: {
          'X-CSRFToken': get_cookie('csrftoken')
        },
        getResponseError: (responseText, xhr) => {
          console.error(this.$tr("uploadError"), responseText);
          alert(this.$tr("uploadError"), responseText);
          this.uppy.reset();
          this.closeModal();
          return new Error(responseText)
        }
      })
      .use(Dashboard, {
        trigger: this.trigger,
        inline: this.inline,
        closeAfterFinish: !!!this.inline,
        target: this.$refs.container,
        replaceTargetContent: true,
        showProgressDetails: true,
        showLinkToFileUploadResult: false,
        proudlyDisplayPoweredByUppy: false,
        closeModalOnClickOutside: true,
        locale: {
          strings: {
            closeModal: this.$tr('closeModal'),
            dashboardTitle: this.$tr('dashboardTitle'),
            dashboardWindowTitle: this.$tr('dashboardWindowTitle'),
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
        }
      })
      .use(Url, {
        target: Dashboard,
        serverUrl: 'https://companion.uppy.io',
        title: this.$tr('link'),
        locale: {
          strings: {
            import: this.$tr('import'),
            enterUrlToImport: this.$tr('enterUrlToImport'),
            failedToFetch: this.$tr('failedToFetch'),
            enterCorrectUrl: this.$tr('enterCorrectUrl')
          }
        }
      })
      .use(GoogleDrive, {
        target: Dashboard,
        serverUrl: 'https://companion.uppy.io'
      })
      .on('file-added', this.addedFile)
      .on('upload-success', this.onUpload)
      .on('upload-error', this.onError)
      .on('file-removed', this.onCancel)
      .run();
    },
    addedFile(file) {
      this.$emit('started', file);
    },
    onUpload(file, response) {
      this.$emit('uploaded', response.body);
      this.uppy.reset();
      this.closeModal();
    },
    onError(file, error, response) {
      this.$emit('error');
    },
    onCancel(file) {
      this.$emit('cancelled', file)
    }
  }
};

</script>


<style lang="less">
@import '../../../../less/global-variables.less';

// Need to use !important a lot because uppy's stylesheet
// has a lot of rules marked as important
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

</style>
