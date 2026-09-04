(function () {
    function init() {
        const wrapper = document.createElement("div");
        wrapper.className = "cm-login-wrapper";

        const hero = document.createElement("div");
        hero.className = "cm-login-hero";
        const logoElement = document.createElement("div");
        logoElement.className = "cm-login-logo";
        logoElement.innerHTML = `
            <img src="/caramia_login/static/src/img/loguito.png" alt="Logo Cara Mía" />
        `;
        hero.appendChild(logoElement);

        const heroContent = document.createElement("div");
        heroContent.className = "cm-hero-content";
        heroContent.innerHTML = `
            <h1 class="cm-hero-title">Gestionar nunca fue tan <strong>simple</strong></h1>
            <h1 class="cm-hero-tagline">Tu negocio, sin complicaciones</h1>
        `;
        hero.appendChild(heroContent);

        const rightPanel = document.createElement("div");
        rightPanel.className = "cm-login-right";

        wrapper.appendChild(hero);
        wrapper.appendChild(rightPanel);

        const canvas = document.createElement("canvas");
        canvas.id = "cm-shader-bg";
        canvas.style.cssText = `
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            z-index: 0; /* Detrás del texto, pero dentro del hero */
            pointer-events: none;
            border: none;
        `;
        hero.insertBefore(canvas, hero.firstChild);

        const wrapwrap = document.getElementById("wrapwrap");
        if (wrapwrap) {
            document.body.insertBefore(wrapper, wrapwrap);
            const loginCard = document.querySelector('.oe_website_login_container') || document.querySelector('.card.border-0');
            if (loginCard) {
                loginCard.style.pointerEvents = "auto";
                rightPanel.appendChild(loginCard);
            }
        }

        const gl = canvas.getContext("webgl");
        if (!gl) return;

        const vert = `
            attribute vec2 a_pos;
            void main() {
                gl_Position = vec4(a_pos, 0.0, 1.0);
            }
        `;

        const frag = `
            precision highp float;
            uniform float u_time;
            uniform vec2  u_res;

            vec3 mod289v3(vec3 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
            vec2 mod289v2(vec2 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
            vec3 permute(vec3 x) { return mod289v3(((x * 34.0) + 1.0) * x); }
            float snoise(vec2 v) {
                const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
                vec2 i  = floor(v + dot(v, C.yy));
                vec2 x0 = v - i + dot(i, C.xx);
                vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
                vec4 x12 = x0.xyxy + C.xxzz;
                x12.xy -= i1;
                i = mod289v2(i);
                vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
                vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
                m = m * m * m * m;
                vec3 x2 = 2.0 * fract(p * C.www) - 1.0;
                vec3 h  = abs(x2) - 0.5;
                vec3 ox = floor(x2 + 0.5);
                vec3 a0 = x2 - ox;
                m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
                vec3 g;
                g.x  = a0.x  * x0.x  + h.x  * x0.y;
                g.yz = a0.yz * x12.xz + h.yz * x12.yw;
                return 130.0 * dot(m, g);
            }

            void main() {
                vec2 uv = gl_FragCoord.xy / u_res;
                
                // Mantiene la velocidad fluida de la animación
                float t  = u_time * 0.4;
                vec2 p = uv * 0.9;
                
                // Generación del ruido base
                float n1 = snoise(p + vec2(t * 0.3,  t * 0.2))  * 1.0;
                float n2 = snoise(p * 1.4 - vec2(t * 0.2, t * 0.15)) * 0.7;
                float n3 = snoise(p * 0.6 + vec2(t * 0.1, t * 0.25)) * 1.2;
                
                float wave = clamp((n1 + n2 + n3) * 0.28 + 0.5, 0.0, 1.0);

                // 1. PALETA DE COLORES OSCURA
                vec3 colorDark = vec3(0.078, 0.086, 0.110); // #14161c (Base oscura principal)
                vec3 colorMid = vec3(0.231, 0.243, 0.275); // #3b3e46 (Tono intermedio para las ondas)
                vec3 colorAcc = vec3(0.545, 0.553, 0.592); // #8b8d97 (Toques de acento sutiles)
                // 2. FONDO BASE
                // Crea un movimiento súper sutil entre negro puro y negro/gris
                vec3 color = mix(colorDark, colorMid, wave);

                // 3. TOQUES MINÚSCULOS DE BLANCO
                // smoothstep(0.85, 1.0) fuerza a que SOLO el 15% más alto de la onda tome el color blanco.
                // Si quieres que haya aún menos blanco, sube el 0.85 a 0.90 o 0.95.
                float whiteTouches = smoothstep(0.6, 1.0, wave);
                color = mix(color, colorAcc, whiteTouches * 0.8);

                // 4. VIÑETA (Opcional)
                // Oscurece sutilmente los bordes para centrar la atención
                float vignette = smoothstep(0.0, 1.2, length(uv - vec2(0.5, 0.5)));
                color = mix(color, vec3(0.0), vignette * 0.7);

                gl_FragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
            }
        `;
        function compile(type, src) {
            const s = gl.createShader(type);
            gl.shaderSource(s, src);
            gl.compileShader(s);
            return s;
        }

        const prog = gl.createProgram();
        gl.attachShader(prog, compile(gl.VERTEX_SHADER, vert));
        gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, frag));
        gl.linkProgram(prog);
        gl.useProgram(prog);

        const buf = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);

        const loc = gl.getAttribLocation(prog, "a_pos");
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

        const uTime = gl.getUniformLocation(prog, "u_time");
        const uRes = gl.getUniformLocation(prog, "u_res");

        function resize() {
            // Ajustamos el canvas al tamaño de su contenedor (.cm-login-hero) no a la ventana
            const rect = hero.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
            gl.viewport(0, 0, canvas.width, canvas.height);
        }

        resize();
        window.addEventListener("resize", resize);

        const t0 = performance.now();
        (function loop() {
            gl.uniform1f(uTime, (performance.now() - t0) / 1000);
            gl.uniform2f(uRes, canvas.width, canvas.height);
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            requestAnimationFrame(loop);
        })();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();