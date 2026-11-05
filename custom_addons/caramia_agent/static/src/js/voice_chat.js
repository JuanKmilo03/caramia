(function () {
    'use strict';

    function initVoice() {
        const historial = document.getElementById('historial-chat-ia');
        const inputChat = document.getElementById('input-chat-ia');
        const btnEnviar = document.getElementById('btn-enviar-ia');
        const inputArea = document.getElementById('input-area-ia');
        if (!historial || !inputChat || !btnEnviar || !inputArea) {
            return false;
        }
        if (inputArea.dataset.voiceReady === '1') {
            return true;
        }
        inputArea.dataset.voiceReady = '1';

        const estado = document.createElement('span');
        estado.id = 'voice-status-ia';
        estado.style.marginLeft = '6px';
        estado.style.fontSize = '12px';
        estado.style.color = '#555';
        inputArea.appendChild(estado);

        const btnMic = document.createElement('button');
        btnMic.id = 'btn-mic-ia';
        btnMic.type = 'button';
        btnMic.title = 'Grabar audio';
        btnMic.textContent = '\uD83C\uDF99';
        btnMic.style.marginLeft = '6px';
        inputArea.appendChild(btnMic);

        const btnStop = document.createElement('button');
        btnStop.id = 'btn-stop-tts-ia';
        btnStop.type = 'button';
        btnStop.title = 'Detener voz';
        btnStop.textContent = '\u23F9';
        btnStop.style.marginLeft = '4px';
        inputArea.appendChild(btnStop);

        let mediaRecorder = null;
        let chunks = [];
        let isRecording = false;

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            btnMic.addEventListener('click', async function () {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                }
                if (isRecording) {
                    mediaRecorder.stop();
                    return;
                }
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    chunks = [];
                    mediaRecorder.ondataavailable = function (e) {
                        if (e.data.size > 0) chunks.push(e.data);
                    };
                    mediaRecorder.onstart = function () {
                        isRecording = true;
                        btnMic.textContent = '\u23F9';
                        estado.textContent = 'Grabando... pulsa para detener';
                    };
                    mediaRecorder.onstop = async function () {
                        isRecording = false;
                        btnMic.textContent = '\uD83C\uDF99';
                        estado.textContent = 'Transcribiendo...';
                        const blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
                        const fd = new FormData();
                        fd.append('file', blob, 'audio.webm');
                        try {
                            const res = await fetch('/caramia/stt', { method: 'POST', body: fd });
                            const data = await res.json();
                            if (data.texto) {
                                inputChat.value = data.texto;
                                estado.textContent = 'Revisa y pulsa Enviar';
                            } else {
                                estado.textContent = 'Error: ' + (data.detail || data.error || JSON.stringify(data));
                            }
                        } catch (e) {
                            console.error(e);
                            estado.textContent = 'Error de conexión';
                        }
                        stream.getTracks().forEach(function (t) { t.stop(); });
                    };
                    mediaRecorder.start();
                } catch (e) {
                    console.error('getUserMedia error', e);
                    estado.textContent = 'Sin permiso de micrófono';
                }
            });
        } else {
            btnMic.style.display = 'none';
            estado.textContent = 'Audio no soportado';
        }

        btnStop.addEventListener('click', function () {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
        });

        // Lectura en voz alta de respuestas del bot
        if ('speechSynthesis' in window) {
            const observer = new MutationObserver(function (mutations) {
                mutations.forEach(function (m) {
                    m.addedNodes.forEach(function (node) {
                        if (node.nodeType !== 1) return;
                        if (!node.classList || !node.classList.contains('msj-ia-bot')) return;
                        const text = (node.textContent || '').trim();
                        if (!text || text.indexOf('Procesando') !== -1) return;
                        try {
                            const utter = new SpeechSynthesisUtterance(text);
                            utter.lang = 'es-CO';
                            window.speechSynthesis.cancel();
                            window.speechSynthesis.speak(utter);
                        } catch (e) {
                            console.error('TTS error', e);
                        }
                    });
                });
            });
            observer.observe(historial, { childList: true, subtree: true });
        }

        return true;
    }

    let attempts = 0;
    const timer = setInterval(function () {
        attempts += 1;
        if (initVoice() || attempts > 50) {
            clearInterval(timer);
        }
    }, 200);
})();