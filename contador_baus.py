import argparse
import json
import math
import os
import queue
import random
import sys
import tkinter as tk

TECLA_MAIS = "f8"
TECLA_MENOS = "f7"
TECLA_ZERAR_SESSAO = "f6"
TECLA_MOVER = "f10"
TECLA_SAIR = "f12"
MARCO = 50
SOM = False

W, H = 300, 124
FUNDO = "#14101f"
OURO = "#ffd54a"
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contador_baus.json")


def fmt(n):
    return f"{n:,}".replace(",", ".")


def mix(c1, c2, k):
    k = max(0.0, min(1.0, k))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def estrela(cx, cy, r1, r2, pontas=4):
    pts = []
    for i in range(pontas * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.pi * i / pontas - math.pi / 2
        pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


def rrect(x1, y1, x2, y2, r):
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


class Contador:
    def __init__(self, root, total_inicial=None):
        self.root = root
        self.fila = queue.Queue()
        self.total = 0
        self.sessao = 0
        self.pos = (40, 40)
        self.carregar()
        if total_inicial is not None:
            self.total = max(0, total_inicial)

        root.title("Contador de Baús")
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.93)
        except tk.TclError:
            pass
        root.geometry(f"{W}x{H}+{self.pos[0]}+{self.pos[1]}")
        root.configure(bg=FUNDO)
        self.c = tk.Canvas(root, width=W, height=H, bg=FUNDO, highlightthickness=0)
        self.c.pack()

        self.mover = False
        self.f = 99
        self.delta = 1
        self.cor_flash = OURO
        self.marco_t = 0
        self.parts = []
        self.flutuantes = []
        self.cx, self.cy = 56, 66

        self.desenhar()
        self.iniciar_teclas()

        self.c.bind("<ButtonPress-1>", self.inicio_arrasto)
        self.c.bind("<B1-Motion>", self.arrastar)
        self.c.bind("<ButtonRelease-1>", lambda e: self.salvar())
        if total_inicial is not None:
            root.after(300, self.salvar)
        root.after(250, lambda: self.estilo_windows(True))
        root.after(1000, self.manter_no_topo)
        self.tick()

    def carregar(self):
        try:
            with open(SAVE, encoding="utf-8") as f:
                d = json.load(f)
            self.total = int(d.get("total", 0))
            self.pos = (int(d.get("x", 40)), int(d.get("y", 40)))
        except (OSError, ValueError, AttributeError):
            pass

    def salvar(self):
        try:
            self.pos = (self.root.winfo_x(), self.root.winfo_y())
            with open(SAVE, "w", encoding="utf-8") as f:
                json.dump({"total": self.total, "x": self.pos[0], "y": self.pos[1]}, f)
        except (OSError, tk.TclError):
            pass

    def desenhar(self):
        c = self.c
        self.painel = c.create_polygon(rrect(3, 3, W - 3, H - 3, 14), smooth=True,
                                       fill="#1b1530", outline=OURO, width=2)
        self.rotulo = c.create_text(W - 20, 17, anchor="e", text="BAÚS ABERTOS",
                                    fill="#b9b2d6", font=("Arial", 9, "bold"))
        self.t_total = c.create_text(W - 20, 56, anchor="e", text=fmt(self.total),
                                     fill="white", font=("Arial", 36, "bold"))
        self.t_sessao = c.create_text(W - 20, 96, anchor="e", fill="#b9b2d6",
                                      font=("Arial", 10), text="")
        self.dica = c.create_text(14, H - 12, anchor="w", fill="#6f6890", font=("Arial", 8), text="")

        self.bau = [
            self.poly([-30, -2, 30, -2, 30, 26, -30, 26], fill="#8b5a2b", outline="#4a2e12", width=2),
            self.poly([-22, -2, -14, -2, -14, 26, -22, 26], fill="#ffc107", outline="#4a2e12"),
            self.poly([14, -2, 22, -2, 22, 26, 14, 26], fill="#ffc107", outline="#4a2e12"),
            self.poly([-5, 4, 5, 4, 5, 16, -5, 16], fill="#ffd54a", outline="#4a2e12"),
        ]
        self.brilho_bau = c.create_oval(0, 0, 0, 0, fill="#fff59d", outline="", state="hidden")
        self.tampa = [
            self.poly([0, 0, 0, -12, 10, -22, 30, -26, 50, -22, 60, -12, 60, 0],
                      fill="#a0662f", outline="#4a2e12", width=2, smooth=True),
            self.poly([22, 0, 30, 0, 30, -26, 22, -25], fill="#ffc107", outline="#4a2e12"),
        ]
        self.atualizar_textos()

    def poly(self, pts, **kw):
        return (self.c.create_polygon(pts, **kw), list(pts))

    def posicionar(self, itens, x, y, ang=0.0):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        for item, pts in itens:
            out = []
            for k in range(0, len(pts), 2):
                px, py = pts[k], pts[k + 1]
                out += [x + px * ca - py * sa, y + px * sa + py * ca]
            self.c.coords(item, *out)

    def atualizar_textos(self):
        self.c.itemconfig(self.t_sessao, text=f"Sessão: {fmt(self.sessao)}")
        if self.mover:
            self.c.itemconfig(self.dica, fill="#ff8a80",
                              text=f"MODO MOVER: arraste a janela  |  {TECLA_MOVER.upper()} trava")
        else:
            self.c.itemconfig(self.dica, fill="#6f6890",
                              text=f"{TECLA_MAIS.upper()} +1   {TECLA_MENOS.upper()} -1   "
                                   f"{TECLA_MOVER.upper()} mover   {TECLA_SAIR.upper()} sair")

    def mudar(self, delta):
        novo = max(0, self.total + delta)
        if novo == self.total:
            return
        self.total = novo
        self.sessao = max(0, self.sessao + delta)
        self.salvar()
        self.delta = delta
        self.f = 0
        self.cor_flash = OURO if delta > 0 else "#ff5252"
        self.atualizar_textos()

        for fl in self.flutuantes:
            self.c.delete(fl[0])
        self.flutuantes = []
        item = self.c.create_text(self.cx, 34, text=("+1" if delta > 0 else "-1"),
                                  fill=self.cor_flash, font=("Arial", 20, "bold"))
        self.flutuantes.append([item, 0])

        if delta > 0:
            for _ in range(10):
                self.brilho(self.cx + rng_u(-30, 30), self.cy + rng_u(-20, 10), v=3.2)
            if SOM:
                self.tocar_som()
            if MARCO and self.total % MARCO == 0:
                self.marco_t = 70
                for _ in range(24):
                    self.brilho(rng_u(20, W - 20), rng_u(10, H - 20), "#ffffff", v=4, vida=34)

    def brilho(self, x, y, cor="#fff8c4", v=0.3, vida=24):
        s = rng_u(4, 9)
        item = self.c.create_polygon(estrela(x, y, s, s * 0.3, 4), fill=cor, outline="")
        self.parts.append([item, rng_u(-v, v), rng_u(-v, v) - 0.6, vida])

    def tocar_som(self):
        try:
            import winsound
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass

    def acao(self, nome):
        if nome == "mais":
            self.mudar(+1)
        elif nome == "menos":
            self.mudar(-1)
        elif nome == "zera":
            self.sessao = 0
            self.atualizar_textos()
        elif nome == "mover":
            self.mover = not self.mover
            self.estilo_windows(not self.mover)
            self.atualizar_textos()
            self.c.itemconfig(self.painel, outline="#ffffff" if self.mover else OURO)
            if not self.mover:
                self.salvar()
        elif nome == "sair":
            self.salvar()
            self.root.destroy()

    def tick(self):
        try:
            while True:
                self.acao(self.fila.get_nowait())
        except queue.Empty:
            pass
        except tk.TclError:
            return

        c = self.c
        f = self.f
        if f < 44:
            u = min(1.0, f / 22)
            s = math.sin(math.pi * u)
            dy = -14 * s if self.delta > 0 else 0
            abre = s if self.delta > 0 else 0
            tam = 36 + int(10 * math.sin(math.pi * min(1.0, f / 14)))
            cor = mix(self.cor_flash, "#ffffff", f / 28)
            dx = math.sin(f * 1.6) * 4 * (1 - f / 44) if self.delta < 0 else 0
            self.f += 1
        else:
            dy, abre, tam, cor, dx = 0, 0, 36, "white", 0

        texto = fmt(self.total)
        tam = min(tam, int(175 / (0.66 * len(texto))))
        c.itemconfig(self.t_total, text=texto, fill=cor, font=("Arial", tam, "bold"))
        c.coords(self.t_total, W - 20 + dx, 56)

        self.posicionar(self.bau, self.cx, self.cy + dy)
        self.posicionar(self.tampa, self.cx - 30, self.cy + dy - 9 * abre, -26 * abre)
        if abre > 0.05:
            w, h = 4 + 20 * abre, 2 + 7 * abre
            c.coords(self.brilho_bau, self.cx - w, self.cy + dy - 2 - h, self.cx + w, self.cy + dy - 2 + h)
            c.itemconfig(self.brilho_bau, state="normal", fill=mix("#ffd54a", "#fff59d", abre))
            c.tag_raise(self.brilho_bau)
            for item, _ in self.tampa:
                c.tag_raise(item)
        else:
            c.itemconfig(self.brilho_bau, state="hidden")

        for fl in self.flutuantes[:]:
            fl[1] += 1
            c.coords(fl[0], self.cx, 34 - fl[1] * 0.75)
            c.itemconfig(fl[0], fill=mix(self.cor_flash, "#1b1530", fl[1] / 36))
            if fl[1] >= 36:
                c.delete(fl[0])
                self.flutuantes.remove(fl)

        vivas = []
        for p in self.parts:
            c.move(p[0], p[1], p[2])
            p[3] -= 1
            if p[3] > 0:
                vivas.append(p)
            else:
                c.delete(p[0])
        self.parts = vivas

        if self.marco_t > 0:
            self.marco_t -= 1
            c.itemconfig(self.rotulo, text=f"★ {fmt(self.total)} BAÚS! ★",
                         fill=OURO if (self.marco_t // 5) % 2 == 0 else "#ffffff")
            c.itemconfig(self.painel, outline="#ffffff" if (self.marco_t // 4) % 2 else OURO)
            if self.marco_t == 0:
                c.itemconfig(self.rotulo, text="BAÚS ABERTOS", fill="#b9b2d6")
                c.itemconfig(self.painel, outline=OURO)

        self.root.after(30, self.tick)

    def manter_no_topo(self):
        try:
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.after(1000, self.manter_no_topo)
        except tk.TclError:
            pass

    def inicio_arrasto(self, e):
        self._dx, self._dy = e.x, e.y

    def arrastar(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")

    def estilo_windows(self, atravessar_cliques):
        if os.name != "nt":
            return
        try:
            import ctypes
            u = ctypes.windll.user32
            hwnd = u.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            GWL_EXSTYLE = -20
            estilo = u.GetWindowLongW(hwnd, GWL_EXSTYLE)
            # LAYERED | TOOLWINDOW | NOACTIVATE (não rouba o foco do jogo)
            estilo |= 0x00080000 | 0x00000080 | 0x08000000
            if atravessar_cliques:
                # TRANSPARENT: o mouse atravessa a janela
                estilo |= 0x00000020
            else:
                estilo &= ~0x00000020
            u.SetWindowLongW(hwnd, GWL_EXSTYLE, estilo)
        except Exception:
            pass

    def iniciar_teclas(self):
        mapa_nomes = {TECLA_MAIS: "mais", TECLA_MENOS: "menos", TECLA_ZERAR_SESSAO: "zera",
                      TECLA_MOVER: "mover", TECLA_SAIR: "sair"}
        try:
            from pynput import keyboard
            mapa = {getattr(keyboard.Key, nome): acao for nome, acao in mapa_nomes.items()}
            apertadas = set()

            def ao_apertar(tecla):
                acao = mapa.get(tecla)
                if acao and tecla not in apertadas:
                    apertadas.add(tecla)
                    self.fila.put(acao)

            def ao_soltar(tecla):
                apertadas.discard(tecla)

            self.listener = keyboard.Listener(on_press=ao_apertar, on_release=ao_soltar)
            self.listener.daemon = True
            self.listener.start()
        except Exception as erro:
            print("Aviso: não consegui ativar os atalhos globais "
                  f"({erro}).\nInstale com:  pip install pynput\n"
                  "Enquanto isso os atalhos só funcionam com esta janela em foco.",
                  file=sys.stderr)
            for nome, acao in mapa_nomes.items():
                self.root.bind(f"<{nome.upper()}>", lambda e, a=acao: self.fila.put(a))
            self.root.focus_force()


def rng_u(a, b):
    return random.uniform(a, b)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Contador de baús em overlay")
    ap.add_argument("--total", type=int, default=None,
                    help="define o total de baús já abertos (ex.: --total 1234)")
    args = ap.parse_args()
    raiz = tk.Tk()
    Contador(raiz, args.total)
    raiz.mainloop()
