import { registry } from "@web/core/registry";
import {
    App,
    Component,
    onMounted,
    onWillUnmount,
    useRef,
    xml,
} from "@odoo/owl";

console.log("CARAMIA SPLASH JS CARGADO");

class SplashScreen extends Component {
    static template = xml`
        <div class="cm-splash-root" t-ref="root">

            <canvas class="cm-splash-canvas" t-ref="canvas"/>

            <div class="cm-splash-blob-tl"/>
            <div class="cm-splash-blob-br"/>

            <div class="cm-splash-center">

                <div class="cm-splash-logo-wrap">
                    <div class="cm-splash-logo-ring"/>
                    <div class="cm-splash-logo-inner">
                        <img
                            t-att-src="props.avatarUrl"
                            t-att-alt="props.userName"
                        />
                    </div>
                </div>
                <div class="cm-splash-greeting">
                    <span class="cm-splash-hello">
                        <t t-esc="props.greeting"/>
                    </span>
                    <t t-if="!props.greeting.includes(props.userName)">
                        <span class="cm-splash-title">
                            <t t-esc="props.userName"/>!
                        </span>
                    </t>
                    <t t-else="">
                        <span class="cm-splash-title">!</span>
                    </t>
                </div>

                <p class="cm-splash-sub">
                    <t t-esc="props.greetingSub"/>
                </p>

                <div class="cm-splash-divider"/>

                <div class="cm-splash-progress-wrap">
                    <div class="cm-splash-track">
                        <div class="cm-splash-fill" t-ref="bar"/>
                    </div>
                    <p class="cm-splash-label">
                        Cargando
                        <span class="cm-dots">
                            <span>.</span>
                            <span>.</span>
                            <span>.</span>
                        </span>
                    </p>
                </div>

            </div>
        </div>
    `;

    static props = {
        onDone: Function,
        userName: String,
        avatarUrl: String,
        greeting: String,
        greetingSub: String,
    };

    setup() {
        this.rootRef = useRef("root");
        this.canvasRef = useRef("canvas");
        this.barRef = useRef("bar");

        this.animationFrame = null;
        this.particleFrame = null;
        this.resizeHandler = null;
        this.alive = true;

        onMounted(() => { this.startSplash(); });

        onWillUnmount(() => {
            this.alive = false;
            if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
            if (this.particleFrame) cancelAnimationFrame(this.particleFrame);
            if (this.resizeHandler) window.removeEventListener("resize", this.resizeHandler);
        });
    }

    startSplash() {
        console.log("🚀 SPLASH ANIMACIÓN INICIADA");

        const DURATION = 1500;
        const FADE = 800;
        const root = this.rootRef.el;
        const bar = this.barRef.el;
        const canvas = this.canvasRef.el;

        if (!root || !bar) {
            console.error("❌ No se encontraron las referencias del splash");
            return;
        }

        const start = performance.now();

        // ── Barra de progreso ────────────────────────────────

        const updateProgress = (now) => {
            if (!this.alive) return;

            const elapsed = now - start;
            const percentage = Math.min((elapsed / DURATION) * 100, 100);
            bar.style.width = `${percentage}%`;

            if (elapsed >= DURATION) {
                console.log("✅ SPLASH TERMINADO");
                root.classList.add("cm-splash-out");
                setTimeout(() => {
                    if (this.alive && this.props.onDone) this.props.onDone();
                }, FADE);
                return;
            }

            this.animationFrame = requestAnimationFrame(updateProgress);
        };

        this.animationFrame = requestAnimationFrame(updateProgress);

        // ── Partículas (doradas) ─────────────────────────────

        if (!canvas) return;

        const ctx = canvas.getContext("2d");

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        this.resizeHandler = resize;
        resize();
        window.addEventListener("resize", resize);

        const particles = Array.from({ length: 45 }, () => ({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            r: Math.random() * 1.4 + 0.3,
            vx: (Math.random() - 0.5) * 0.2,
            vy: -(Math.random() * 0.35 + 0.08),
            a: Math.random() * 0.22 + 0.05,
        }));

        const drawParticles = () => {
            if (!this.alive) return;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            for (const p of particles) {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(235, 173, 51, ${p.a})`;
                ctx.fill();

                p.x += p.vx;
                p.y += p.vy;

                if (p.y < -10) { p.y = canvas.height + 10; p.x = Math.random() * canvas.width; }
                if (p.x < -10) p.x = canvas.width + 10;
                if (p.x > canvas.width + 10) p.x = -10;
            }

            this.particleFrame = requestAnimationFrame(drawParticles);
        };

        drawParticles();
    }
}

// saludo cambia diariamente
const GREETING_VARIANTS = [
    { main: "Hola de nuevo,", sub: "Tu espacio de trabajo está listo" },
    { main: "¡A trabajar,", sub: "Muchas cosas por hacer hoy" },
    { main: "¿Qué haremos hoy,", sub: "Todo listo para empezar" },
];

function pickGreeting(name) {
    const seed = `${new Date().toISOString().slice(0, 10)}-${name}`;
    let hash = 0;
    for (const ch of seed) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
    return GREETING_VARIANTS[hash % GREETING_VARIANTS.length];
}


const splashService = {
    dependencies: ["action"],

    async start(env) {
        console.log("🚀 SERVICIO CARAMIA INICIADO");

        const params = new URLSearchParams(window.location.search);
        if (params.get("splash") !== "1") return {};

        const cleanUrl = window.location.pathname;
        window.history.replaceState(null, "", cleanUrl);

        // ── Datos de sesión ──────────────────────────────────

        let uid = null;
        let name = "Usuario";

        try {
            const response = await fetch("/web/session/get_session_info", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
            });

            const data = await response.json();
            console.log("🔍 session info:", data?.result);

            if (data?.result) {
                uid = data.result.uid;
                name = data.result.name.split(" ")[0];
            }
        } catch (e) {
            console.warn("⚠️ No se pudo obtener la sesión:", e);
        }

        const avatarUrl = uid
            ? `/web/image/res.users/${uid}/avatar_128?unique=${Date.now()}`
            : "/web/static/img/avatar.png";

        const { main: greeting, sub: greetingSub } = pickGreeting(name);

        console.log("👤 USUARIO:", name, "| SALUDO:", greeting);

        // ── Montar splash ────────────────────────────────────

        const mountSplash = () => new Promise((resolve) => {
            const container = document.createElement("div");
            container.id = "caramia-splash-container";
            Object.assign(container.style, {
                position: "fixed",
                inset: "0",
                zIndex: "999999",
            });
            document.body.appendChild(container);

            const app = new App(SplashScreen, {
                props: {
                    userName: name,
                    avatarUrl,
                    greeting,
                    greetingSub,
                    onDone: () => {
                        app.destroy();
                        container.remove();
                        resolve();
                    },
                },
                env,
            });

            app.mount(container);
        });

        mountSplash();
        return {};
    },
};

registry.category("services").add("caramia_splash", splashService);