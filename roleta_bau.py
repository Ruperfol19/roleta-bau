import json
import math
import os
import random
import tkinter as tk

TESTE = False

W, H = 900, 700
CX, CY = 285, 350
RAIO = 215
SEGMENTOS = 24
PASSO = 360 / SEGMENTOS
OX = W // 2
FUNDO = "#0b0816"
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roleta_save.json")

rng = random.SystemRandom()

PREMIOS = [
    dict(id="token",     nome="Token Dourado",      chance=137_500,   cor="#ffb300", seg=0),
    dict(id="acessorio", nome="Picareta / Mochila", chance=568,       cor="#ff7043", seg=3),
    dict(id="veiculo",   nome="Veículo + Decalque", chance=7_813,     cor="#e53935", seg=6),
    dict(id="musica",    nome="Música",             chance=391,       cor="#ec407a", seg=9),
    dict(id="skin",      nome="Skin de Ouro",       chance=1_562_500, cor="#fff59d", seg=12),
    dict(id="wallpaper", nome="Tela de Wallpaper",  chance=272,       cor="#26c6da", seg=15),
    dict(id="elemental", nome="Item de Elementais", chance=127,       cor="#66bb6a", seg=18),
]
PREMIOS_RARIDADE = sorted(PREMIOS, key=lambda p: -p["chance"])
SEG_PREMIO = {p["seg"]: p for p in PREMIOS}
SEG_VAZIOS = [i for i in range(SEGMENTOS) if i not in SEG_PREMIO]

ELEMENTOS = {
    "fogo":  dict(nome="FOGO",  cor="#ff6d00", cor2="#ffd600", tit="#ff9100"),
    "água":  dict(nome="ÁGUA",  cor="#29b6f6", cor2="#e1f5fe", tit="#4fc3f7"),
    "ar":    dict(nome="AR",    cor="#b2ebf2", cor2="#ffffff", tit="#b2ebf2"),
    "terra": dict(nome="TERRA", cor="#8d6e63", cor2="#66bb6a", tit="#81c784"),
}

CORES_CONFETE = ["#ffd54a", "#ff4d4d", "#4dd0e1", "#81c784", "#ba68c8", "#ffffff"]

FLAMA = [0, -60, 20, -30, 38, -5, 40, 25, 25, 50, 0, 58, -25, 50, -40, 25, -35, -5, -18, -30]
FLAMA_INT = [0, -25, 14, 0, 18, 28, 0, 45, -18, 28, -14, 0]
GOTA = [0, -62, 14, -35, 34, -5, 38, 22, 26, 46, 0, 56, -26, 46, -38, 22, -34, -5, -14, -35]
GOTA_BRILHO = [-24, 6, -16, 6, -16, 30, -24, 30]
CRISTAL_E = [0, -58, -40, -30, -40, 25, 0, 58]
CRISTAL_D = [0, -58, 40, -30, 40, 25, 0, 58]
CRISTAL_T = [0, -58, 40, -30, 0, -5, -40, -30]
ESPIRAL = [v for k in range(90)
           for v in ((3 + k * 0.6) * math.cos(k * 0.2), (3 + k * 0.6) * math.sin(k * 0.2))]


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


def ease_out_back(u):
    return 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2


class App:
    def __init__(self, root):
        self.root = root
        root.title("Roleta do Baú")
        root.resizable(False, False)
        self.c = tk.Canvas(root, width=W, height=H, bg="#14101f", highlightthickness=0)
        self.c.pack()

        self.girando = False
        self.overlay = False
        self.overlay_id = 0
        self.t = 0
        self.parts = []
        self.angulo = 0.0
        self._tremor = (0, 0)
        self.arcos = []
        self.pid = None
        self.sub = None
        self.carregar()

        self.c.create_text(W / 2, 40, text="ROLETA DO BAÚ", fill="#ffd54a",
                           font=("Arial", 28, "bold"))
        self.c.create_text(W / 2, 76, text="Clique no baú para girar e tentar a sorte!",
                           fill="#b9b2d6", font=("Arial", 12))

        self.desenhar_roleta()
        self.desenhar_bau()
        self.desenhar_painel()

        self.txt_info = self.c.create_text(CX, 615, text="Clique no baú para girar!",
                                           fill="white", font=("Arial", 15, "bold"))
        self.txt_cont = self.c.create_text(CX, 650, fill="#b9b2d6", font=("Arial", 12),
                                           text=f"Tentativas: {fmt(self.tentativas)}")

        self.c.bind("<Button-1>", self.clique)
        self.c.tag_bind("bau", "<Enter>", lambda e: self.c.config(cursor="hand2"))
        self.c.tag_bind("bau", "<Leave>", lambda e: self.c.config(cursor=""))
        if TESTE:
            self.c.create_text(10, H - 10, anchor="sw", fill="#ff8a80", font=("Arial", 10),
                               text="MODO TESTE: teclas 1 a 7 mostram cada animação")
            root.bind("<Key>", self.tecla)

    def carregar(self):
        self.tentativas = 0
        self.contagem = {p["id"]: 0 for p in PREMIOS}
        try:
            with open(SAVE, encoding="utf-8") as f:
                d = json.load(f)
            self.tentativas = int(d.get("tentativas", 0))
            for k, v in d.get("premios", {}).items():
                if k in self.contagem:
                    self.contagem[k] = int(v)
        except (OSError, ValueError, AttributeError):
            pass

    def salvar(self):
        try:
            with open(SAVE, "w", encoding="utf-8") as f:
                json.dump({"tentativas": self.tentativas, "premios": self.contagem}, f)
        except OSError:
            pass

    def desenhar_roleta(self):
        for i in range(SEGMENTOS):
            cor = SEG_PREMIO[i]["cor"] if i in SEG_PREMIO else ["#6c3fc4", "#2b1f55"][i % 2]
            self.arcos.append(self.c.create_arc(
                CX - RAIO, CY - RAIO, CX + RAIO, CY + RAIO, start=0, extent=PASSO,
                fill=cor, outline="#14101f", width=2))
        self.atualizar_roleta()
        self.c.create_oval(CX - RAIO - 6, CY - RAIO - 6, CX + RAIO + 6, CY + RAIO + 6,
                           outline="#ffd54a", width=6)
        self.c.create_oval(CX - 95, CY - 95, CX + 95, CY + 95, fill="#14101f",
                           outline="#ffd54a", width=4)
        self.c.create_polygon(CX - 18, CY - RAIO - 22, CX + 18, CY - RAIO - 22,
                              CX, CY - RAIO + 20, fill="#ff4d4d", outline="white", width=2)

    def atualizar_roleta(self):
        for i, arco in enumerate(self.arcos):
            self.c.itemconfig(arco, start=(self.angulo + i * PASSO) % 360)

    def desenhar_bau(self):
        x, y, t = CX, CY + 5, "bau"
        self.c.create_rectangle(x - 60, y - 5, x + 60, y + 50, fill="#8b5a2b",
                                outline="#4a2e12", width=3, tags=t)
        self.c.create_arc(x - 60, y - 50, x + 60, y + 30, start=0, extent=180,
                          fill="#a0662f", outline="#4a2e12", width=3, tags=t)
        for dx in (-38, 38):
            self.c.create_rectangle(x + dx - 6, y - 28, x + dx + 6, y + 50,
                                    fill="#ffc107", outline="#4a2e12", tags=t)
        self.c.create_rectangle(x - 10, y - 12, x + 10, y + 12, fill="#ffd54a",
                                outline="#4a2e12", width=2, tags=t)
        self.c.create_oval(x - 3, y - 4, x + 3, y + 2, fill="#4a2e12", tags=t)

    def desenhar_painel(self):
        c, x0 = self.c, 570
        c.create_rectangle(555, 105, 885, 580, fill="#1b1530", outline="#3a2f63", width=2)
        c.create_text(720, 130, text="PRÊMIOS", fill="#ffd54a", font=("Arial", 16, "bold"))
        self.txt_premio = {}
        y = 160
        for p in PREMIOS_RARIDADE:
            c.create_rectangle(x0, y + 2, x0 + 16, y + 18, fill=p["cor"], outline="white")
            c.create_text(x0 + 26, y, anchor="nw", text=p["nome"], fill="white",
                          font=("Arial", 11, "bold"))
            c.create_text(x0 + 26, y + 19, anchor="nw", text=f"1 em {fmt(p['chance'])}",
                          fill="#b9b2d6", font=("Arial", 9))
            self.txt_premio[p["id"]] = c.create_text(
                870, y + 12, anchor="e", text=f"x{self.contagem[p['id']]}",
                fill="#ffd54a", font=("Arial", 13, "bold"))
            y += 58

    def clique(self, e):
        if self.overlay:
            if self.t > 25:
                self.fechar_overlay()
            return
        if self.girando or math.hypot(e.x - CX, e.y - CY) > 100:
            return
        self.girar()

    def tecla(self, e):
        if self.girando or self.overlay:
            return
        if e.char.isdigit() and 1 <= int(e.char) <= len(PREMIOS):
            self.mostrar_premio(PREMIOS[int(e.char) - 1])

    def girar(self):
        self.girando = True
        self.tentativas += 1
        self.c.itemconfig(self.txt_cont, text=f"Tentativas: {fmt(self.tentativas)}")
        self.c.itemconfig(self.txt_info, text="Girando...", fill="white")

        # o resultado é decidido aqui; a roleta apenas anima até o segmento sorteado
        premio = None
        for p in PREMIOS_RARIDADE:
            if rng.randint(1, p["chance"]) == 1:
                premio = p
                break

        alvo = premio["seg"] if premio else rng.choice(SEG_VAZIOS)
        final = (90 - PASSO / 2 - alvo * PASSO) % 360
        total = 360 * 4 + (final - self.angulo) % 360
        self.animar_giro(0, 100, self.angulo, total, premio)

    def animar_giro(self, frame, frames, inicio, total, premio):
        t = frame / frames
        self.angulo = (inicio + total * (1 - (1 - t) ** 3)) % 360
        self.atualizar_roleta()

        dx, dy = rng.uniform(-2, 2) * (1 - t), rng.uniform(-2, 2) * (1 - t)
        self.c.move("bau", dx - self._tremor[0], dy - self._tremor[1])
        self._tremor = (dx, dy)

        if frame < frames:
            self.root.after(25, self.animar_giro, frame + 1, frames, inicio, total, premio)
        else:
            self.c.move("bau", -self._tremor[0], -self._tremor[1])
            self._tremor = (0, 0)
            self.fim_giro(premio)

    def fim_giro(self, premio):
        self.girando = False
        if premio:
            self.contagem[premio["id"]] += 1
            self.c.itemconfig(self.txt_premio[premio["id"]],
                              text=f"x{self.contagem[premio['id']]}")
        self.salvar()
        if premio:
            self.mostrar_premio(premio)
        else:
            self.c.itemconfig(self.txt_info, text="Não foi dessa vez... tente de novo!",
                              fill="#b9b2d6")

    def mostrar_premio(self, p):
        self.c.itemconfig(self.txt_info, text=f"Você ganhou: {p['nome']}!", fill=p["cor"])
        self.overlay = True
        self.overlay_id += 1
        self.t = 0
        self.parts = []
        self.pid = p["id"]
        self.sub = None
        if self.pid == "acessorio":
            self.sub = rng.choice(["picareta", "mochila"])
        elif self.pid == "elemental":
            self.sub = rng.choice(list(ELEMENTOS))
        self.c.create_rectangle(0, 0, W, H, fill=FUNDO, outline="", tags="overlay")
        getattr(self, "setup_" + self.pid)()
        self.c.create_text(OX, 677, text="(clique para fechar)", fill="#8a84a8",
                           font=("Arial", 11), tags="overlay")
        self.tick(self.overlay_id)

    def tick(self, oid):
        if not self.overlay or oid != self.overlay_id:
            return
        getattr(self, "anim_" + self.pid)(self.t)
        self.atualizar_particulas()
        self.c.itemconfig(self.tit2, fill=self.tit2_cor if (self.t // 6) % 2 == 0 else "white")
        self.t += 1
        self.root.after(30, self.tick, oid)

    def fechar_overlay(self):
        self.overlay = False
        self.parts = []
        self.c.delete("overlay")
        self.c.itemconfig(self.txt_info, text="Clique no baú para girar!", fill="white")

    def titulo(self, l1, l2, cor, f1=28, f2=34):
        self.tit2_cor = cor
        self.c.create_text(OX, 515, text=l1, fill="white", font=("Arial", f1, "bold"),
                           tags="overlay")
        self.tit2 = self.c.create_text(OX, 565, text=l2, fill=cor, font=("Arial", f2, "bold"),
                                       tags="overlay")

    def particula(self, item, vx, vy, ay=0.0, vida=60):
        self.parts.append([item, vx, vy, ay, vida])

    def atualizar_particulas(self):
        vivas = []
        for p in self.parts:
            p[2] += p[3]
            self.c.move(p[0], p[1], p[2])
            p[4] -= 1
            if p[4] > 0:
                vivas.append(p)
            else:
                self.c.delete(p[0])
        self.parts = vivas

    def confete(self):
        x, s = rng.uniform(0, W), rng.randint(6, 12)
        item = self.c.create_rectangle(x, -10, x + s, -10 + s, fill=rng.choice(CORES_CONFETE),
                                       outline="", tags="overlay")
        self.particula(item, rng.uniform(-1.5, 1.5), rng.uniform(3, 7), 0, 160)

    def brilho(self, x, y, cor="#fff8c4", v=0.3, vida=22):
        s = rng.uniform(6, 14)
        item = self.c.create_polygon(estrela(x, y, s, s * 0.25, 4), fill=cor, outline="",
                                     tags="overlay")
        self.particula(item, rng.uniform(-v, v), -0.6 + rng.uniform(-v, v), 0, vida)

    def poly(self, pts, **kw):
        return (self.c.create_polygon(pts, tags="overlay", **kw), list(pts))

    def linha(self, pts, **kw):
        return (self.c.create_line(pts, tags="overlay", **kw), list(pts))

    def posicionar(self, itens, x, y, ang=0.0, sx=1.0, sy=1.0):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        for item, pts in itens:
            out = []
            for k in range(0, len(pts), 2):
                px, py = pts[k] * sx, pts[k + 1] * sy
                out += [x + px * ca - py * sa, y + px * sa + py * ca]
            self.c.coords(item, *out)

    def raios_luz(self, cor, largura=16):
        return [self.c.create_line(0, 0, 0, 0, fill=cor, width=largura, tags="overlay")
                for _ in range(12)]

    def girar_raios(self, t, cy):
        for i, r in enumerate(self.raios):
            a = math.radians(t * 1.2 + i * 30)
            self.c.coords(r, OX, cy, OX + math.cos(a) * 600, cy + math.sin(a) * 600)

    def setup_token(self):
        c = self.c
        self.raios = self.raios_luz("#3d2f0a")
        self.m_ext = c.create_oval(0, 0, 1, 1, fill="#ffc107", outline="#b8860b", width=5,
                                   tags="overlay")
        self.m_int = c.create_oval(0, 0, 1, 1, fill="#ffe082", outline="#b8860b", width=2,
                                   tags="overlay")
        self.m_txt = c.create_text(OX, 270, text="★", fill="#b8860b",
                                   font=("Arial", 70, "bold"), tags="overlay")
        self.titulo("VOCÊ GANHOU", "O TOKEN DOURADO!", "#ffd54a", 30, 36)

    def anim_token(self, t):
        c = self.c
        cy = 270 + math.sin(t * 0.08) * 8
        self.girar_raios(t, cy)
        larg = max(4, abs(math.cos(t * 0.1)) * 85)
        c.coords(self.m_ext, OX - larg, cy - 85, OX + larg, cy + 85)
        c.coords(self.m_int, OX - larg * 0.78, cy - 66, OX + larg * 0.78, cy + 66)
        c.coords(self.m_txt, OX, cy)
        c.itemconfig(self.m_txt, state="normal" if larg > 35 else "hidden")
        for _ in range(2):
            self.confete()

    def setup_skin(self):
        c = self.c
        self.raios = self.raios_luz("#2e2508", 18)
        c.create_oval(OX - 110, 450, OX + 110, 485, fill="#3d2f0a", outline="#ffd54a",
                      width=2, tags="overlay")
        kw = dict(fill="#c9971c", outline="#fff3b0", width=2, tags="overlay")
        self.skin = [
            (c.create_oval(OX - 32, 175, OX + 32, 240, **kw), 207),
            (c.create_polygon(OX - 55, 250, OX + 55, 250, OX + 45, 350, OX - 45, 350, **kw), 300),
            (c.create_polygon(OX - 82, 258, OX - 55, 250, OX - 48, 340, OX - 76, 346, **kw), 300),
            (c.create_polygon(OX + 82, 258, OX + 55, 250, OX + 48, 340, OX + 76, 346, **kw), 300),
            (c.create_polygon(OX - 45, 350, OX - 4, 350, OX - 6, 455, OX - 48, 455, **kw), 400),
            (c.create_polygon(OX + 45, 350, OX + 4, 350, OX + 6, 455, OX + 48, 455, **kw), 400),
        ]
        self.titulo("VOCÊ GANHOU A", "SKIN DE OURO!", "#ffd54a", 30, 36)

    def anim_skin(self, t):
        self.girar_raios(t, 320)
        varredura = 150 + (t * 6) % 420
        base = 0.15 + 0.1 * math.sin(t * 0.15)
        for item, yc in self.skin:
            k = math.exp(-((yc - varredura) / 45) ** 2)
            self.c.itemconfig(item, fill=mix("#c9971c", "#ffffff", base + k))
        if t % 3 == 0:
            self.brilho(OX + rng.uniform(-110, 110), rng.uniform(170, 460))

    def setup_veiculo(self):
        c = self.c
        c.create_rectangle(0, 440, W, 480, fill="#25252f", outline="", tags="overlay")
        self.faixas = [c.create_rectangle(0, 0, 0, 0, fill="#bdbdbd", outline="", tags="overlay")
                       for _ in range(8)]
        self.estrada = 0.0
        self.carro = [
            self.poly([-120, 405, -120, 372, -80, 365, -50, 335, 40, 335, 75, 365, 120, 372, 120, 405],
                      fill="#e53935", outline="#7f0000", width=3),
            self.poly([-60, 366, -40, 342, -5, 342, -5, 366], fill="#b3e5fc", outline="#7f0000", width=2),
            self.poly([5, 366, 5, 342, 36, 342, 58, 366], fill="#b3e5fc", outline="#7f0000", width=2),
            self.poly([105, 376, 118, 376, 118, 390, 105, 390], fill="#fff59d", outline="#f9a825"),
            self.poly([-120, 380, -112, 380, -112, 392, -120, 392], fill="#ff5252", outline=""),
        ]
        self.rodas = []
        for dx in (-70, 70):
            pneu = c.create_oval(0, 0, 1, 1, fill="#212121", outline="#000000", width=2, tags="overlay")
            aro = c.create_oval(0, 0, 1, 1, fill="#b0bec5", outline="#607d8b", width=2, tags="overlay")
            raios = [c.create_line(0, 0, 0, 0, fill="#455a64", width=3, tags="overlay") for _ in range(4)]
            self.rodas.append((dx, pneu, aro, raios))
        self.decalque = c.create_polygon(0, 0, 0, 0, 0, 0, fill="#ffeb3b", outline="#d50000",
                                         width=3, state="hidden", tags="overlay")
        self.titulo("VOCÊ GANHOU UM VEÍCULO", "COM DECALQUE EXCLUSIVO!", "#ff5252", 26, 30)

    def anim_veiculo(self, t):
        c = self.c
        if t < 60:
            u = t / 60
            x = -200 + (OX + 200) * (1 - (1 - u) ** 3)
            vel = 14 * (1 - u)
            dy = math.sin(t * 0.9) * 1.5
            if t % 2 == 0:
                y = rng.uniform(345, 430)
                self.particula(c.create_line(x - 130, y, x - 180, y, fill="white", width=2,
                                             tags="overlay"), -10, 0, 0, 12)
        else:
            x, vel = OX, 0
            dy = -4 * abs(math.sin((t - 60) * 0.25)) * math.exp(-(t - 60) / 18)

        self.estrada += vel
        for i, f in enumerate(self.faixas):
            fx = (i * 130 - self.estrada) % (W + 130) - 65
            c.coords(f, fx, 457, fx + 70, 462)
        self.posicionar(self.carro, x, dy)
        for dx, pneu, aro, raios in self.rodas:
            wx, wy = x + dx, 412 + dy
            c.coords(pneu, wx - 28, wy - 28, wx + 28, wy + 28)
            c.coords(aro, wx - 17, wy - 17, wx + 17, wy + 17)
            for k, r in enumerate(raios):
                a = x / 28 + k * math.pi / 2
                c.coords(r, wx, wy, wx + math.cos(a) * 17, wy + math.sin(a) * 17)

        if t >= 60:
            u = min(1, (t - 60) / 20)
            r = 28 * ease_out_back(u)
            c.itemconfig(self.decalque, state="normal")
            c.coords(self.decalque, *estrela(x - 5, 388 + dy, r, r * 0.55, 8))
            if t == 60:
                for _ in range(12):
                    self.brilho(x - 5, 388, "#ffeb3b", v=4)

    def setup_acessorio(self):
        c = self.c
        if self.sub == "picareta":
            c.create_rectangle(0, 440, W, 480, fill="#2b2415", outline="", tags="overlay")
            self.rocha = c.create_polygon(OX + 105, 440, OX + 122, 405, OX + 160, 390, OX + 200, 406,
                                          OX + 218, 440, fill="#757575", outline="#424242",
                                          width=3, tags="overlay")
            self.pica = [
                self.poly([-7, 0, 7, 0, 6, -220, -6, -220], fill="#8d5a2b", outline="#4a2e12", width=2),
                self.poly([-85, -200, -60, -228, -25, -244, 0, -248, 25, -244, 60, -228, 85, -200,
                           62, -212, 28, -224, 0, -228, -28, -224, -62, -212],
                          fill="#b0bec5", outline="#37474f", width=2),
                self.poly([-9, -234, 9, -234, 9, -212, -9, -212], fill="#37474f", outline=""),
            ]
            self.titulo("VOCÊ GANHOU UMA", "PICARETA ESPECIAL!", "#ff7043")
        else:
            self.sombra = c.create_oval(0, 0, 1, 1, fill="#1b1730", outline="", tags="overlay")
            borda, azul, escuro, claro = "#123646", "#2e7d9a", "#1f5a73", "#4db6d6"
            self.mochila = [
                self.linha([-20, -70, -20, -92, 20, -92, 20, -70], fill=borda, width=8, smooth=True),
                self.poly(rrect(-82, 10, -58, 62, 8), fill=escuro, outline=borda, width=3, smooth=True),
                self.poly(rrect(58, 10, 82, 62, 8), fill=escuro, outline=borda, width=3, smooth=True),
                self.poly(rrect(-65, -70, 65, 80, 22), fill=azul, outline=borda, width=3, smooth=True),
                self.poly(rrect(-65, -70, 65, -12, 22), fill=escuro, outline=borda, width=3, smooth=True),
                self.poly(rrect(-46, 22, 46, 68, 12), fill=claro, outline=borda, width=3, smooth=True),
                self.poly(rrect(-11, -30, 11, -2, 4), fill="#ffd54a", outline="#8a6d00", width=2, smooth=True),
                self.linha([-46, 45, 46, 45], fill=borda, width=2),
            ]
            self.titulo("VOCÊ GANHOU UMA", "MOCHILA EXCLUSIVA!", "#4dd0e1")

    def anim_acessorio(self, t):
        c = self.c
        if self.sub == "picareta":
            ciclo = t % 48
            if ciclo <= 34:
                ang = -45 + 110 * (ciclo / 34) ** 3
            else:
                ang = 65 - 110 * (ciclo - 34) / 14
            self.posicionar(self.pica, OX - 70, 440, ang)
            c.itemconfig(self.rocha, fill="#fffde7" if 34 <= ciclo <= 37 else "#757575")
            if ciclo == 34:
                for _ in range(16):
                    i = c.create_rectangle(0, 0, 5, 5, outline="", tags="overlay",
                                           fill=rng.choice(["#ffeb3b", "#ffffff", "#ff9800"]))
                    c.move(i, OX + 150, 425)
                    self.particula(i, rng.uniform(-6, 6), rng.uniform(-10, -3), 0.6, 28)
                for _ in range(7):
                    s = rng.randint(6, 11)
                    i = c.create_rectangle(0, 0, s, s, fill="#9e9e9e", outline="#616161",
                                           tags="overlay")
                    c.move(i, OX + 150, 420)
                    self.particula(i, rng.uniform(-4, 5), rng.uniform(-8, -3), 0.7, 30)
        else:
            h = 260 * math.exp(-t / 14) * abs(math.cos(t * 0.28))
            self.posicionar(self.mochila, OX, 300 - h, 6 * math.sin(t * 0.12))
            sw = 85 * (1 - h / 500)
            c.coords(self.sombra, OX - sw, 388, OX + sw, 404)
            if t >= 30 and t % 4 == 0:
                self.brilho(OX + rng.uniform(-120, 120), rng.uniform(190, 390), "#b3e5fc")

    def setup_musica(self):
        c = self.c
        self.disco = c.create_oval(0, 0, 1, 1, fill="#121212", outline="#333333", width=3, tags="overlay")
        self.sulcos = [c.create_oval(0, 0, 1, 1, outline="#2a2a2a", width=1, tags="overlay")
                       for _ in range(4)]
        self.rotulo = c.create_oval(0, 0, 1, 1, fill="#ec407a", outline="#f8bbd0", width=2, tags="overlay")
        self.furo = c.create_oval(0, 0, 1, 1, fill=FUNDO, outline="", tags="overlay")
        self.reflexos = [c.create_arc(0, 0, 1, 1, start=0, extent=30, style="arc",
                                      outline="#9e9e9e", width=5, tags="overlay") for _ in range(2)]
        self.marca = c.create_line(0, 0, 0, 0, fill="white", width=4, tags="overlay")
        self.barras = [c.create_rectangle(0, 0, 0, 0, outline="", tags="overlay",
                                          fill=mix("#ec407a", "#26c6da", i / 15)) for i in range(16)]
        self.titulo("VOCÊ GANHOU UMA", "NOVA MÚSICA!", "#f48fb1")

    def anim_musica(self, t):
        c, cy = self.c, 265
        s = 1 + 0.03 * abs(math.sin(t * 0.22))

        def circ(item, r):
            c.coords(item, OX - r, cy - r, OX + r, cy + r)

        circ(self.disco, 110 * s)
        for k, i in enumerate(self.sulcos):
            circ(i, (95 - 15 * k) * s)
        circ(self.rotulo, 38 * s)
        circ(self.furo, 6)
        ang = t * 6
        for k, a in enumerate(self.reflexos):
            circ(a, 100 * s)
            c.itemconfig(a, start=(ang + k * 180) % 360)
        ar = math.radians(ang)
        c.coords(self.marca, OX, cy, OX + 32 * math.cos(ar), cy - 32 * math.sin(ar))

        for i, b in enumerate(self.barras):
            h = 12 + 75 * abs(math.sin(t * 0.22 + i * 0.7)) * (0.5 + 0.5 * math.sin(t * 0.07 + i))
            x = OX - 240 + i * 30
            c.coords(b, x, 470 - h, x + 22, 470)

        if t % 7 == 0:
            i = c.create_text(OX + rng.uniform(-170, 170), 330, text=rng.choice(["♪", "♫"]),
                              fill=rng.choice(["#f48fb1", "#80deea", "#fff59d", "#ffffff"]),
                              font=("Arial", rng.randint(26, 40), "bold"), tags="overlay")
            self.particula(i, rng.uniform(-1, 1), -2.2, 0, 70)

    def setup_wallpaper(self):
        c = self.c
        x1, x2, y1, y2 = OX - 210, OX + 210, 130, 400
        for i in range(9):
            c.create_rectangle(x1, y1 + i * 30, x2, y1 + (i + 1) * 30,
                               fill=mix("#0d1b4c", "#ff8a3d", i / 8), outline="", tags="overlay")
        self.estrelas = [c.create_oval(0, 0, 1, 1, fill="white", outline="", tags="overlay")
                         for _ in range(14)]
        self.pos_estrelas = [(rng.uniform(x1 + 10, x2 - 10), rng.uniform(y1 + 8, y1 + 90))
                             for _ in range(14)]
        self.sol = c.create_oval(0, 0, 1, 1, fill="#ffe082", outline="#fff8e1", width=3, tags="overlay")
        c.create_polygon(x1, 400, x1, 340, OX - 150, 290, OX - 90, 335, OX - 20, 280, OX + 50, 340,
                         OX + 110, 300, x2, 350, x2, 400, fill="#2d2a5a", outline="", tags="overlay")
        c.create_polygon(x1, 400, x1, 370, OX - 120, 330, OX - 40, 372, OX + 40, 345, OX + 130, 375,
                         x2, 355, x2, 400, fill="#1a1638", outline="", tags="overlay")
        self.cortina = c.create_rectangle(x1, y1, x2, y2, fill=FUNDO, outline="", tags="overlay")
        self.borda_luz = c.create_line(x1, y1, x1, y2, fill="white", width=3, tags="overlay")
        for a in ((x1 - 12, y1 - 12, x2 + 12, y1), (x1 - 12, y2, x2 + 12, y2 + 12),
                  (x1 - 12, y1 - 12, x1, y2 + 12), (x2, y1 - 12, x2 + 12, y2 + 12)):
            c.create_rectangle(*a, fill="#cfd8dc", outline="#455a64", width=2, tags="overlay")
        c.create_polygon(OX - 30, 412, OX + 30, 412, OX + 50, 440, OX - 50, 440,
                         fill="#90a4ae", outline="#455a64", width=2, tags="overlay")
        c.create_rectangle(OX - 80, 440, OX + 80, 452, fill="#cfd8dc", outline="#455a64",
                           width=2, tags="overlay")
        self.titulo("VOCÊ GANHOU UMA NOVA", "TELA DE WALLPAPER!", "#4dd0e1", 26, 32)

    def anim_wallpaper(self, t):
        c = self.c
        x1, x2, y1, y2 = OX - 210, OX + 210, 130, 400
        p = min(1, t / 50)
        borda = x1 + 420 * (1 - (1 - p) ** 3)
        c.coords(self.cortina, borda, y1, x2, y2)
        c.coords(self.borda_luz, borda, y1, borda, y2)
        if p >= 1:
            c.itemconfig(self.borda_luz, state="hidden")
        sy = 372 - 137 * (1 - (1 - min(1, max(0, (t - 20) / 60))) ** 3)
        c.coords(self.sol, OX + 26, sy - 34, OX + 94, sy + 34)
        for k, (sx, sy2) in enumerate(self.pos_estrelas):
            r = 1.5 + 1.2 * abs(math.sin(t * 0.1 + k))
            c.coords(self.estrelas[k], sx - r, sy2 - r, sx + r, sy2 + r)
        if t >= 50 and t % 6 == 0:
            self.brilho(rng.uniform(x1 + 10, x2 - 10), rng.uniform(y1 + 10, y2 - 60), "#ffffff")

    def setup_elemental(self):
        c, e, sub = self.c, ELEMENTOS[self.sub], self.sub
        self.aneis = [c.create_oval(0, 0, 1, 1, outline=e["cor"], width=3, tags="overlay")
                      for _ in range(3)]
        self.nucleo = c.create_oval(0, 0, 1, 1, fill=mix(e["cor"], FUNDO, 0.6), outline=e["cor"],
                                    width=4, tags="overlay")
        if sub == "fogo":
            self.icone = [self.poly(FLAMA, fill="#ff6d00", outline="#ffab40", width=3, smooth=True),
                          self.poly(FLAMA_INT, fill="#ffd600", outline="", smooth=True)]
        elif sub == "água":
            self.icone = [self.poly(GOTA, fill="#29b6f6", outline="#e1f5fe", width=3, smooth=True),
                          self.poly(GOTA_BRILHO, fill="#e1f5fe", outline="", smooth=True)]
        elif sub == "ar":
            self.icone = [self.linha(ESPIRAL, fill="#ffffff", width=6, smooth=True),
                          self.linha([-v for v in ESPIRAL], fill="#80deea", width=6, smooth=True)]
        else:
            self.icone = [self.poly(CRISTAL_E, fill="#6d4c41", outline="#4e342e", width=3),
                          self.poly(CRISTAL_D, fill="#8d6e63", outline="#4e342e", width=3),
                          self.poly(CRISTAL_T, fill="#a1887f", outline="#4e342e", width=3)]
        self.titulo("VOCÊ GANHOU UM ITEM", f"ELEMENTAL DE {e['nome']}!", e["tit"], 28, 32)

    def anim_elemental(self, t):
        c, e, sub, cy = self.c, ELEMENTOS[self.sub], self.sub, 270
        for k, a in enumerate(self.aneis):
            ph = (t * 0.02 + k / 3) % 1
            r = 70 + ph * 130
            c.coords(a, OX - r, cy - r, OX + r, cy + r)
            c.itemconfig(a, outline=mix(e["cor"], FUNDO, ph))
        r = 74 + 4 * math.sin(t * 0.2)
        c.coords(self.nucleo, OX - r, cy - r, OX + r, cy + r)

        bob = 4 * math.sin(t * 0.1)
        if sub == "fogo":
            self.posicionar(self.icone, OX, cy + bob, 0, 1 + 0.06 * math.sin(t * 0.5),
                            1 + 0.08 * math.sin(t * 0.37 + 1))
        elif sub == "água":
            self.posicionar(self.icone, OX, cy + bob, 0, 1 + 0.04 * math.sin(t * 0.2), 1)
        elif sub == "ar":
            self.posicionar(self.icone, OX, cy, t * 4)
        else:
            self.posicionar(self.icone, OX, cy + bob, 4 * math.sin(t * 0.1))

        for _ in range(2):
            if sub == "fogo":
                x, y = OX + rng.uniform(-70, 70), cy + 60
                i = c.create_oval(x - 6, y - 6, x + 6, y + 6, outline="", tags="overlay",
                                  fill=rng.choice(["#ff6d00", "#ffd600", "#ff3d00"]))
                self.particula(i, rng.uniform(-.7, .7), rng.uniform(-6, -3), 0, 40)
            elif sub == "água":
                x = rng.uniform(OX - 220, OX + 220)
                i = c.create_oval(x - 4, 90, x + 4, 104, outline="", tags="overlay",
                                  fill=rng.choice(["#29b6f6", "#81d4fa", "#e1f5fe"]))
                self.particula(i, 0, rng.uniform(4, 7), 0.2, 55)
            elif sub == "ar":
                y = rng.uniform(110, 440)
                i = c.create_line(-60, y, 0, y, width=2, tags="overlay",
                                  fill=rng.choice(["#ffffff", "#b2ebf2"]))
                self.particula(i, rng.uniform(18, 26), 0, 0, 45)
            else:
                x, y, s = rng.uniform(OX - 220, OX + 220), 470, rng.randint(8, 16)
                i = c.create_polygon(x, y, x + s, y - s * 0.3, x + s * 0.8, y + s * 0.8,
                                     x - s * 0.2, y + s, outline="#3e2723", tags="overlay",
                                     fill=rng.choice(["#8d6e63", "#66bb6a", "#a1887f"]))
                self.particula(i, rng.uniform(-2, 2), rng.uniform(-14, -9), 0.6, 40)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
