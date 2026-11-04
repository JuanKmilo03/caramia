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

        // Boton de microfono
        const btnMic = document.createElement('button');
        btnMic.id = 'btn-mic-ia';
        btnMic.type = 'button';
        btnMic.title = 'Hablar';
        btnMic.textContent = '\uD83C\uDF99';
        btnMic.style.marginLeft = '6px';
        inputArea.appendChild(btnMic);

        // Boton para detener la voz
        const btnStop = document.createElement('button');
        btnStop.id = 'btn-stop-tts-ia';
        btnStop.type = 'button';
        btnStop.title = 'Detener voz';
        btnStop.textContent = '\u23F9';
        btnStop.style.marginLeft = '4px';
        inputArea.appendChild(btnStop);

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let isListening = false;
        let finalTranscript = '';

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'es-ES';
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;
            recognition.continuous = false;

            btnMic.addEventListener('click', function () {
                // Cancelar voz actual
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                }
                if (isListening) {
                    recognition.stop();
                    return;
                }
                finalTranscript = '';
                inputChat.value = '';
                isListening = true;
                btnMic.textContent = '\uD83D\uDD34';
                try {
                    recognition.start();
                } catch (e) {
                    console.error('Speech start error', e);
                    isListening = false;
                    btnMic.textContent = '\uD83C\uDF99';
                }
            });

            recognition.onresult = function (event) {
                let interim = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const t = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += t + ' ';
                    } else {
                        interim += t;
                    }
                }
                inputChat.value = (finalTranscript + interim).trim();
            };

            recognition.onend = function () {
                isListening = false;
                btnMic.textContent = '\uD83C\uDF99';
                const msg = (finalTranscript || inputChat.value).trim();
                if (msg) {
                    inputChat.value = msg;
                    // Enviar una sola vez
                    btnEnviar.click();
                }
                finalTranscript = '';
            };

            recognition.onerror = function (event) {
                isListening = false;
                btnMic.textContent = '\uD83C\uDF99';
                console.error('Speech recognition error', event.error);
            };
        } else {
            btnMic.style.display = 'none';
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
                            utter.lang = 'es-ES';
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