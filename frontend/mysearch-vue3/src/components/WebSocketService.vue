<template>
  <div>
    <h2>WebSocket 服务</h2>
    <div id="output"></div>
    <div id="reportContainer"></div>
    <div id="reportActions">
      <div class="alert alert-info" role="alert" id="status"></div>
      <a id="copyToClipboard" @click="copyToClipboard" class="btn btn-secondary mt-3" style="margin-right: 10px;">复制到剪贴板 (Markdown)</a>
      <a id="downloadLinkMd" :href="downloadLinkMd" class="btn btn-secondary mt-3" style="margin-right: 10px;" target="_blank">下载为 Markdown</a>
      <a id="downloadLink" :href="downloadLinkPdf" class="btn btn-secondary mt-3" style="margin-right: 10px;" target="_blank">下载为 PDF</a>
      <a id="downloadLinkWord" :href="downloadLinkWord" class="btn btn-secondary mt-3" target="_blank">下载为 Docx</a>
    </div>
  </div>
</template>

<script>
import showdown from 'showdown';

export default {
  data() {
    return {
      socket: null,
      converter: new showdown.Converter(),
      downloadLinkPdf: '',
      downloadLinkWord: '',
      downloadLinkMd: '',
    };
  },
  mounted() {
    this.initWebSocket();
  },
  methods: {
    initWebSocket() {
      const ws_uri = "ws://localhost:8000/ws";
      this.socket = new WebSocket(ws_uri);

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Received message:", data);  // Debug log
        if (data.type === 'logs') {
          this.addAgentResponse(data);
        } else if (data.type === 'images') {
          console.log("Received images:", data);  // Debug log
          this.displaySelectedImages(data);
        } else if (data.type === 'report') {
          this.writeReport(data);
        } else if (data.type === 'path') {
          this.updateState('finished');
          this.updateDownloadLink(data);
        }
      };

      this.socket.onopen = (event) => {
        console.log(event)
      };
    },
    addAgentResponse(data) {
      const output = document.getElementById('output');
      output.innerHTML += '<div class="agent_response">' + data.output + '</div>';
      output.scrollTop = output.scrollHeight;
      output.style.display = 'block';
      this.updateScroll();
    },
    writeReport(data) {
      const reportContainer = document.getElementById('reportContainer');
      const markdownOutput = this.converter.makeHtml(data.output);
      reportContainer.innerHTML += markdownOutput;
      this.updateScroll();
    },
    updateDownloadLink(data) {
      this.downloadLinkPdf = data.output.pdf;
      this.downloadLinkWord = data.output.docx;
      this.downloadLinkMd = data.output.md;
    },
    updateScroll() {
      window.scrollTo(0, document.body.scrollHeight);
    },
    copyToClipboard() {
      const textarea = document.createElement('textarea');
      textarea.id = 'temp_element';
      textarea.style.height = 0;
      document.body.appendChild(textarea);
      textarea.value = document.getElementById('reportContainer').innerText;
      const selector = document.querySelector('#temp_element');
      selector.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    },
    updateState(state) {
      let status = '';
      switch (state) {
        case 'in_progress':
          status = 'Research in progress...';
          this.setReportActionsStatus('disabled');
          break;
        case 'finished':
          status = 'Research finished!';
          this.setReportActionsStatus('enabled');
          break;
        case 'error':
          status = 'Research failed!';
          this.setReportActionsStatus('disabled');
          break;
        case 'initial':
          status = '';
          this.setReportActionsStatus('hidden');
          break;
        default:
          this.setReportActionsStatus('disabled');
      }
      document.getElementById('status').innerHTML = status;
      if (document.getElementById('status').innerHTML == '') {
        document.getElementById('status').style.display = 'none';
      } else {
        document.getElementById('status').style.display = 'block';
      }
    },
    setReportActionsStatus(status) {
      const reportActions = document.getElementById('reportActions');
      if (status == 'enabled') {
        reportActions.querySelectorAll('a').forEach((link) => {
          link.classList.remove('disabled');
          link.removeAttribute('onclick');
          reportActions.style.display = 'block';
        });
      } else {
        reportActions.querySelectorAll('a').forEach((link) => {
          link.classList.add('disabled');
          link.setAttribute('onclick', 'return false;');
        });
        if (status == 'hidden') {
          reportActions.style.display = 'none';
        }
      }
    },
    displaySelectedImages(data) {
      const imageContainer = document.getElementById('selectedImagesContainer');
      const images = JSON.parse(data.output);
      console.log("Received images:", images);  // Debug log
      if (images && images.length > 0) {
        images.forEach(imageUrl => {
          const imgElement = document.createElement('img');
          imgElement.src = imageUrl;
          imgElement.alt = 'Research Image';
          imgElement.style.maxWidth = '200px';
          imgElement.style.margin = '5px';
          imgElement.style.cursor = 'pointer';
          imgElement.onclick = () => this.showImageDialog(imageUrl);
          imageContainer.appendChild(imgElement);
        });
        imageContainer.style.display = 'block';
      } else {
        imageContainer.innerHTML += '<p>No images found for this research.</p>';
      }
    },
    showImageDialog(imageUrl) {
      const dialog = document.createElement('div');
      dialog.className = 'image-dialog';

      const img = document.createElement('img');
      img.src = imageUrl;
      img.alt = 'Full-size Research Image';

      const closeBtn = document.createElement('button');
      closeBtn.textContent = 'Close';
      closeBtn.onclick = () => document.body.removeChild(dialog);

      dialog.appendChild(img);
      dialog.appendChild(closeBtn);
      document.body.appendChild(dialog);
    },
  },
};
</script>

<style scoped>
.image-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
}

.image-dialog img {
  max-width: 80%;
  max-height: 80%;
}

.image-dialog button {
  position: absolute;
  top: 10px;
  right: 10px;
}
</style>