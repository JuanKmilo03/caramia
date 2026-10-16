// Esperamos a que la interfaz de Odoo cargue completamente
window.addEventListener('load', function() {
    
    // 1. Inyectamos el HTML del widget directamente en el body de Odoo
    const chatHTML = `
        <div id="btn-abrir-chat-ia">🤖</div>
        <div id="panel-chat-ia">
            <div id="header-chat-ia">Asistente Cara Mia</div>
            <div id="historial-chat-ia">
                <div class="msj-ia-bot">¡Hola! Soy tu asistente de IA. ¿En qué te ayudo?</div>
            </div>
            <div id="input-area-ia">
                <input type="text" id="input-chat-ia" placeholder="Escribe aquí..."/>
                <button id="btn-enviar-ia">Enviar</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', chatHTML);

    // 2. Lógica para abrir/cerrar el panel
    const btnAbrir = document.getElementById('btn-abrir-chat-ia');
    const panelChat = document.getElementById('panel-chat-ia');
    const historial = document.getElementById('historial-chat-ia');
    const inputChat = document.getElementById('input-chat-ia');
    const btnEnviar = document.getElementById('btn-enviar-ia');

    btnAbrir.addEventListener('click', () => {
        panelChat.style.display = panelChat.style.display === 'flex' ? 'none' : 'flex';
        if(panelChat.style.display === 'flex') inputChat.focus();
    });

    // 3. Lógica para enviar el mensaje
    function enviarMensaje() {
        const mensaje = inputChat.value.trim();
        if (!mensaje) return;

        // Mostrar mensaje del usuario
        historial.innerHTML += `<div class="msj-ia-user">${mensaje}</div>`;
        inputChat.value = '';
        historial.scrollTop = historial.scrollHeight;

        // Indicador de carga
        const idCarga = 'carga_' + Date.now();
        historial.innerHTML += `<div id="${idCarga}" class="msj-ia-bot"><i>Procesando...</i></div>`;
        historial.scrollTop = historial.scrollHeight;

        // Llamar a nuestro controlador de Python en Odoo
        fetch('/caramia/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: { mensaje: mensaje }
            })
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById(idCarga).remove();
            let respuesta = data.result.respuesta || "Error de comunicación";
            respuesta = respuesta.replace(/\n/g, '<br>'); // Formatear saltos de línea
            historial.innerHTML += `<div class="msj-ia-bot">${respuesta}</div>`;
            historial.scrollTop = historial.scrollHeight;
        })
        .catch(err => {
            document.getElementById(idCarga).remove();
            historial.innerHTML += `<div class="msj-ia-bot" style="color:red;">Error de conexión.</div>`;
        });
    }

    btnEnviar.addEventListener('click', enviarMensaje);
    inputChat.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') enviarMensaje();
    });
});