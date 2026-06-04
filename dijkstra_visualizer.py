
import tkinter as tk
from tkinter import messagebox
import random
import math
import heapq

CANVAS_W = 900
CANVAS_H = 620

VERTEX_RADIUS = 22
EDGE_COLOR = "#78909C"
EDGE_WIDTH = 2
WEIGHT_COLOR = "#37474F"

COLOR_DEFAULT = "#1565C0"     # обычная вершина
COLOR_SELECTED = "#FF6F00"    # старт / финиш
COLOR_VISITED = "#6A1B9A"     # посещена алгоритмом
COLOR_CURRENT = "#C62828"     # текущая в алгоритме
COLOR_PATH = "#2E7D32"        # кратчайший путь
COLOR_EDGE_PATH = "#43A047"   # ребро кратчайшего пути

AXIS_COLOR = "#B0BEC5"
GRID_COLOR = "#ECEFF1"

ANIMATION_DELAY = 600          # мс между шагами анимации


class Graph:
    """Хранит вершины и рёбра, реализует алгоритм Дейкстры."""

    def __init__(self):
        self.vertices = {}    # id -> (x, y, label)
        self.edges = []       # [(id1, id2, weight), ...]
        self._next_id = 0

    def clear(self):
        self.vertices.clear()
        self.edges.clear()
        self._next_id = 0

    def add_vertex(self, x, y):
        """Добавить вершину, вернуть её id."""
        vid = self._next_id
        label = str(vid)
        self.vertices[vid] = (x, y, label)
        self._next_id += 1
        return vid

    def add_edge(self, v1, v2, weight):
        """Добавить ребро (без дублей)."""
        for (a, b, w) in self.edges:
            if (a == v1 and b == v2) or (a == v2 and b == v1):
                return  # уже есть
        self.edges.append((v1, v2, weight))

    def remove_vertex(self, vid):
        if vid in self.vertices:
            del self.vertices[vid]
            self.edges = [e for e in self.edges if e[0] != vid and e[1] != vid]

    def get_adjacency(self):
        """Вернуть словарь смежности: {vid: [(сосед, вес), ...]}"""
        adj = {vid: [] for vid in self.vertices}
        for (v1, v2, w) in self.edges:
            adj[v1].append((v2, w))
            adj[v2].append((v1, w))
        return adj

    def dijkstra(self, start, end):
        """
          dist  — словарь расстояний,
          prev  — словарь предшественников,
          order — список шагов [(вершина, множество_посещённых), ...]
        """
        adj = self.get_adjacency()
        dist = {vid: math.inf for vid in self.vertices}
        dist[start] = 0
        prev = {vid: None for vid in self.vertices}
        visited = set()
        order = []  # порядок извлечения из очереди

        # heap: (расстояние, id вершины)
        heap = [(0, start)]

        while heap:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)
            order.append((u, set(visited)))

            if u == end:
                break

            for (v, w) in adj[u]:
                if v not in visited:
                    new_dist = dist[u] + w
                    if new_dist < dist[v]:
                        dist[v] = new_dist
                        prev[v] = u
                        heapq.heappush(heap, (new_dist, v))

        # Восстановить путь
        path = []
        cur = end
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()

        if path[0] != start:
            path = []  # путь не найден

        return dist, prev, order, path

class AddVertexDialog(tk.Toplevel):
    """Всплывающее окно для ввода X, Y новой вершины."""

    def __init__(self, parent, callback, max_x, max_y):
        super().__init__(parent)
        self.title("Добавить вершину")
        self.resizable(False, False)
        self.grab_set()
        self.callback = callback

        self.geometry("280x170")
        self.configure(bg="#F5F5F5")

        tk.Label(self, text="Введите координаты вершины",
                 bg="#F5F5F5", font=("Arial", 11, "bold")).pack(pady=(16, 8))

        frame = tk.Frame(self, bg="#F5F5F5")
        frame.pack(padx=20, fill="x")

        tk.Label(frame, text=f"X (0–{max_x}):", bg="#F5F5F5").grid(
            row=0, column=0, sticky="w", pady=4)
        self.x_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.x_var, width=10).grid(
            row=0, column=1, padx=8)

        tk.Label(frame, text=f"Y (0–{max_y}):", bg="#F5F5F5").grid(
            row=1, column=0, sticky="w", pady=4)
        self.y_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.y_var, width=10).grid(
            row=1, column=1, padx=8)

        self.max_x = max_x
        self.max_y = max_y

        btn_frame = tk.Frame(self, bg="#F5F5F5")
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Добавить", command=self._ok,
                  bg="#1565C0", fg="white", width=10).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Отмена", command=self.destroy,
                  width=10).pack(side="left", padx=6)

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _ok(self):
        try:
            x = int(self.x_var.get())
            y = int(self.y_var.get())
        except ValueError:
            messagebox.showerror(
                "Ошибка", "X и Y должны быть целыми числами.", parent=self)
            return
        if not (0 <= x <= self.max_x and 0 <= y <= self.max_y):
            messagebox.showerror(
                "Ошибка",
                f"Координаты должны быть в диапазоне X: 0–{self.max_x}, Y: 0–{self.max_y}.",
                parent=self)
            return
        self.callback(x, y)
        self.destroy()

class GenerateDialog(tk.Toplevel):
    """Диалог настроек случайного графа."""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Генерация графа")
        self.resizable(False, False)
        self.grab_set()
        self.callback = callback

        self.geometry("300x220")
        self.configure(bg="#F5F5F5")

        tk.Label(self, text="Параметры случайного графа",
                 bg="#F5F5F5", font=("Arial", 11, "bold")).pack(pady=(16, 8))

        frame = tk.Frame(self, bg="#F5F5F5")
        frame.pack(padx=20, fill="x")

        fields = [
            ("Количество вершин (2–15):", "n_var", "7"),
            ("Мин. вес ребра:", "wmin_var", "1"),
            ("Макс. вес ребра:", "wmax_var", "20"),
            ("Вероятность ребра (0.1–1.0):", "prob_var", "0.5"),
        ]

        self.vars = {}
        for i, (label, var_name, default) in enumerate(fields):
            tk.Label(frame, text=label, bg="#F5F5F5", anchor="w").grid(
                row=i, column=0, sticky="w", pady=3)
            v = tk.StringVar(value=default)
            self.vars[var_name] = v
            tk.Entry(frame, textvariable=v, width=8).grid(
                row=i, column=1, padx=8)

        btn_frame = tk.Frame(self, bg="#F5F5F5")
        btn_frame.pack(pady=14)
        tk.Button(btn_frame, text="Сгенерировать", command=self._ok,
                  bg="#2E7D32", fg="white", width=14).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Отмена", command=self.destroy,
                  width=10).pack(side="left", padx=6)

    def _ok(self):
        try:
            n = int(self.vars["n_var"].get())
            wmin = int(self.vars["wmin_var"].get())
            wmax = int(self.vars["wmax_var"].get())
            prob = float(self.vars["prob_var"].get())
        except ValueError:
            messagebox.showerror(
                "Ошибка", "Проверьте правильность введённых значений.", parent=self)
            return

        if not (2 <= n <= 15):
            messagebox.showerror(
                "Ошибка", "Количество вершин: 2–15.", parent=self)
            return
        if wmin > wmax or wmin < 1:
            messagebox.showerror(
                "Ошибка", "Веса рёбер должны быть >= 1, и wmin <= wmax.", parent=self)
            return
        if not (0.1 <= prob <= 1.0):
            messagebox.showerror(
                "Ошибка", "Вероятность ребра: 0.1–1.0.", parent=self)
            return

        self.callback(n, wmin, wmax, prob)
        self.destroy()

class DijkstraApp:
    """Главный класс приложения."""

    def __init__(self, root):
        self.root = root
        self.root.title("Визуализатор алгоритма Дейкстры")
        self.root.configure(bg="#ECEFF1")
        self.root.resizable(False, False)

        self.graph = Graph()

        self.start_vertex = None
        self.end_vertex = None
        self.mode = "add"        # "add", "start", "end", "edge_from"
        self.edge_from = None    # первая вершина для добавления ребра

        self.path_edges = set()   # рёбра пути для подсветки
        self.path_vertices = set()
        self.visited_vertices = set()
        self.current_vertex = None

        self._animation_steps = []
        self._anim_index = 0
        self._anim_job = None

        self._build_ui()

    def _build_ui(self):
        # Левая панель инструментов
        left = tk.Frame(self.root, bg="#37474F", width=200)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="🗺  Дейкстра", bg="#37474F", fg="white",
                 font=("Arial", 14, "bold")).pack(pady=(18, 4))
        tk.Label(left, text="Визуализатор", bg="#37474F", fg="#90A4AE",
                 font=("Arial", 9)).pack(pady=(0, 16))

        self._sep(left)

        # Режимы
        tk.Label(left, text="РЕЖИМ КЛИКА", bg="#37474F", fg="#90A4AE",
                 font=("Arial", 8)).pack(anchor="w", padx=12, pady=(10, 2))

        self.mode_var = tk.StringVar(value="add")
        modes = [
            ("➕  Добавить вершину", "add"),
            ("🟠  Выбрать старт", "start"),
            ("🔴  Выбрать финиш", "end"),
            ("──  Добавить ребро", "edge_from"),
        ]
        for text, val in modes:
            rb = tk.Radiobutton(left, text=text, variable=self.mode_var,
                                value=val, command=self._on_mode_change,
                                bg="#37474F", fg="white", selectcolor="#1565C0",
                                activebackground="#37474F", activeforeground="white",
                                font=("Arial", 10), anchor="w")
            rb.pack(fill="x", padx=12, pady=2)

        self._sep(left)

        # Действия
        tk.Label(left, text="ДЕЙСТВИЯ", bg="#37474F", fg="#90A4AE",
                 font=("Arial", 8)).pack(anchor="w", padx=12, pady=(10, 2))

        buttons = [
            ("Добавить по XY", self._open_add_dialog, "#1565C0"),
            ("Сгенерировать граф", self._open_generate_dialog, "#4527A0"),
            ("Запустить алгоритм", self._run_algorithm, "#2E7D32"),
            ("Показать результат", self._show_result_instantly, "#00695C"),
            ("Очистить граф", self._clear_graph, "#B71C1C"),
        ]
        for text, cmd, color in buttons:
            tk.Button(left, text=text, command=cmd, bg=color, fg="white",
                      font=("Arial", 10), anchor="w", padx=10,
                      relief="flat", cursor="hand2",
                      activebackground=color, activeforeground="white"
                      ).pack(fill="x", padx=12, pady=3, ipady=4)

        self._sep(left)

        # Информация
        tk.Label(left, text="ИНФОРМАЦИЯ", bg="#37474F", fg="#90A4AE",
                 font=("Arial", 8)).pack(anchor="w", padx=12, pady=(10, 2))

        self.info_label = tk.Label(left, text="Кликайте на холст,\nчтобы добавлять\nвершины.",
                                   bg="#37474F", fg="#CFD8DC",
                                   font=("Arial", 9), justify="left", wraplength=170)
        self.info_label.pack(padx=12, pady=4, anchor="w")

        # Легенда
        self._sep(left)
        tk.Label(left, text="ЛЕГЕНДА", bg="#37474F", fg="#90A4AE",
                 font=("Arial", 8)).pack(anchor="w", padx=12, pady=(10, 2))

        legend = [
            (COLOR_DEFAULT,  "Вершина"),
            (COLOR_SELECTED, "Старт / Финиш"),
            (COLOR_VISITED,  "Посещена"),
            (COLOR_CURRENT,  "Текущая"),
            (COLOR_PATH,     "Путь"),
        ]
        for color, label in legend:
            row = tk.Frame(left, bg="#37474F")
            row.pack(anchor="w", padx=12, pady=1)
            tk.Label(row, bg=color, width=3, height=1).pack(side="left")
            tk.Label(row, text=f"  {label}", bg="#37474F", fg="#CFD8DC",
                     font=("Arial", 9)).pack(side="left")

        # Правая часть — холст
        right = tk.Frame(self.root, bg="#ECEFF1")
        right.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(right, width=CANVAS_W, height=CANVAS_H,
                                bg="white", highlightthickness=1,
                                highlightbackground="#B0BEC5", cursor="crosshair")
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Строка состояния
        self.status_var = tk.StringVar(
            value="Готов. Выберите режим и кликните на холст.")
        status_bar = tk.Label(right, textvariable=self.status_var,
                              bg="#37474F", fg="white", font=("Arial", 9),
                              anchor="w", padx=10)
        status_bar.pack(fill="x", side="bottom", padx=10, pady=(0, 10))

        self._draw_axes()

    def _sep(self, parent):
        tk.Frame(parent, bg="#546E7A", height=1).pack(
            fill="x", padx=12, pady=4)

    def _draw_axes(self):
        """Нарисовать оси и сетку на фоне."""
        self.canvas.delete("axis")

        step = 50
        # Вертикальные линии
        for x in range(0, CANVAS_W, step):
            self.canvas.create_line(x, 0, x, CANVAS_H,
                                    fill=GRID_COLOR, tags="axis")
            if x > 0:
                self.canvas.create_text(x, CANVAS_H - 8, text=str(x),
                                        fill=AXIS_COLOR, font=("Arial", 7),
                                        tags="axis")
        # Горизонтальные линии
        for y in range(0, CANVAS_H, step):
            self.canvas.create_line(0, y, CANVAS_W, y,
                                    fill=GRID_COLOR, tags="axis")
            if y > 0:
                self.canvas.create_text(8, y, text=str(y),
                                        fill=AXIS_COLOR, font=("Arial", 7),
                                        tags="axis")

        # Основные оси (потолще)
        self.canvas.create_line(0, CANVAS_H // 2, CANVAS_W, CANVAS_H // 2,
                                fill=AXIS_COLOR, width=1, tags="axis")
        self.canvas.create_line(CANVAS_W // 2, 0, CANVAS_W // 2, CANVAS_H,
                                fill=AXIS_COLOR, width=1, tags="axis")

        # Подписи осей
        self.canvas.create_text(CANVAS_W - 15, CANVAS_H // 2 - 10,
                                text="X", fill="#78909C",
                                font=("Arial", 10, "bold"), tags="axis")
        self.canvas.create_text(CANVAS_W // 2 + 12, 10,
                                text="Y", fill="#78909C",
                                font=("Arial", 10, "bold"), tags="axis")

    def _redraw(self):
        """Полная перерисовка графа."""
        self.canvas.delete("graph")
        self._draw_axes()
        self._draw_edges()
        self._draw_vertices()

    def _get_vertex_color(self, vid):
        if vid == self.current_vertex:
            return COLOR_CURRENT
        if vid in self.path_vertices:
            return COLOR_PATH
        if vid in self.visited_vertices:
            return COLOR_VISITED
        if vid == self.start_vertex or vid == self.end_vertex:
            return COLOR_SELECTED
        return COLOR_DEFAULT

    def _draw_vertices(self):
        for vid, (x, y, label) in self.graph.vertices.items():
            color = self._get_vertex_color(vid)
            r = VERTEX_RADIUS

            # Тень
            self.canvas.create_oval(x - r + 3, y - r + 3, x + r + 3, y + r + 3,
                                    fill="#B0BEC5", outline="", tags="graph")
            # Основной круг
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    fill=color, outline="white", width=2,
                                    tags="graph")
            # Подпись (номер)
            self.canvas.create_text(x, y, text=label,
                                    fill="white", font=("Arial", 11, "bold"),
                                    tags="graph")
            # Маркер старта / финиша
            if vid == self.start_vertex:
                self.canvas.create_text(x, y - r - 10, text="START",
                                        fill=COLOR_SELECTED,
                                        font=("Arial", 8, "bold"), tags="graph")
            elif vid == self.end_vertex:
                self.canvas.create_text(x, y - r - 10, text="END",
                                        fill="#C62828",
                                        font=("Arial", 8, "bold"), tags="graph")

    def _draw_edges(self):
        for (v1, v2, weight) in self.graph.edges:
            if v1 not in self.graph.vertices or v2 not in self.graph.vertices:
                continue
            x1, y1, _ = self.graph.vertices[v1]
            x2, y2, _ = self.graph.vertices[v2]

            is_path_edge = (
                (v1, v2) in self.path_edges or (v2, v1) in self.path_edges
            )
            color = COLOR_EDGE_PATH if is_path_edge else EDGE_COLOR
            width = 4 if is_path_edge else EDGE_WIDTH

            self.canvas.create_line(x1, y1, x2, y2,
                                    fill=color, width=width,
                                    tags="graph")

            # Вес — посередине ребра
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            self.canvas.create_rectangle(mx - 12, my - 8, mx + 12, my + 8,
                                         fill="white", outline=EDGE_COLOR,
                                         tags="graph")
            self.canvas.create_text(mx, my, text=str(weight),
                                    fill=WEIGHT_COLOR,
                                    font=("Arial", 8, "bold"), tags="graph")

    def _on_mode_change(self):
        self.mode = self.mode_var.get()
        self.edge_from = None
        hints = {
            "add": "Кликните на холст — добавится вершина.",
            "start": "Кликните на вершину, чтобы выбрать её как СТАРТ.",
            "end": "Кликните на вершину, чтобы выбрать её как ФИНИШ.",
            "edge_from": "Кликните на первую вершину ребра.",
        }
        self._set_status(hints.get(self.mode, ""))

    def _on_canvas_click(self, event):
        x, y = event.x, event.y

        if self.mode == "add":
            self._add_vertex_at(x, y)
        elif self.mode == "start":
            vid = self._find_vertex_at(x, y)
            if vid is not None:
                self.start_vertex = vid
                self._set_status(f"Старт: вершина {vid}")
                self._reset_algo_state()
                self._redraw()
        elif self.mode == "end":
            vid = self._find_vertex_at(x, y)
            if vid is not None:
                self.end_vertex = vid
                self._set_status(f"Финиш: вершина {vid}")
                self._reset_algo_state()
                self._redraw()
        elif self.mode == "edge_from":
            vid = self._find_vertex_at(x, y)
            if vid is None:
                return
            if self.edge_from is None:
                self.edge_from = vid
                self._set_status(
                    f"Первая вершина: {vid}. Теперь кликните на вторую вершину.")
            else:
                if self.edge_from == vid:
                    self._set_status(
                        "Нельзя соединить вершину саму с собой. Выберите другую.")
                    return
                # Запрашиваем вес через простой диалог
                self._ask_weight(self.edge_from, vid)
                self.edge_from = None

    def _ask_weight(self, v1, v2):
        """Диалог ввода веса ребра."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Вес ребра")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.geometry("240x120")
        dlg.configure(bg="#F5F5F5")

        tk.Label(dlg, text=f"Вес ребра {v1} — {v2}:",
                 bg="#F5F5F5", font=("Arial", 10)).pack(pady=(16, 4))
        w_var = tk.StringVar(value="1")
        entry = tk.Entry(dlg, textvariable=w_var, width=10, font=("Arial", 11))
        entry.pack()
        entry.focus_set()

        def ok():
            try:
                w = int(w_var.get())
                if w < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Ошибка", "Вес должен быть целым числом >= 1.", parent=dlg)
                return
            self.graph.add_edge(v1, v2, w)
            self._redraw()
            self._set_status(f"Добавлено ребро {v1}–{v2} с весом {w}.")
            dlg.destroy()

        dlg.bind("<Return>", lambda e: ok())
        tk.Button(dlg, text="Ок", command=ok,
                  bg="#1565C0", fg="white", width=8).pack(pady=8)

    def _add_vertex_at(self, x, y):
        """Добавить вершину, проверив на перекрытие."""
        for (vx, vy, _) in self.graph.vertices.values():
            dist = math.hypot(x - vx, y - vy)
            if dist < VERTEX_RADIUS * 2:
                self._set_status(
                    "Слишком близко к другой вершине. Выберите другое место.")
                return
        vid = self.graph.add_vertex(x, y)
        self._reset_algo_state()
        self._redraw()
        self._set_status(f"Добавлена вершина {vid} в ({x}, {y}).")

    def _find_vertex_at(self, x, y):
        """Найти вершину по координатам клика."""
        for vid, (vx, vy, _) in self.graph.vertices.items():
            if math.hypot(x - vx, y - vy) <= VERTEX_RADIUS:
                return vid
        self._set_status("Вершина не найдена в этой точке.")
        return None

    def _open_add_dialog(self):
        AddVertexDialog(self.root, self._add_vertex_from_dialog,
                        CANVAS_W, CANVAS_H)

    def _add_vertex_from_dialog(self, x, y):
        self._add_vertex_at(x, y)

    def _open_generate_dialog(self):
        GenerateDialog(self.root, self._generate_graph)

    def _generate_graph(self, n, wmin, wmax, prob):
        self._clear_graph()
        margin = 60
        # Расставляем вершины случайно, избегая перекрытий
        positions = []
        attempts = 0
        while len(positions) < n and attempts < 2000:
            attempts += 1
            x = random.randint(margin, CANVAS_W - margin)
            y = random.randint(margin, CANVAS_H - margin)
            ok = all(math.hypot(x - px, y - py) >= VERTEX_RADIUS * 3
                     for px, py in positions)
            if ok:
                positions.append((x, y))

        for (x, y) in positions:
            self.graph.add_vertex(x, y)

        ids = list(self.graph.vertices.keys())
        # Гарантируем связность — соединяем по цепочке
        for i in range(len(ids) - 1):
            w = random.randint(wmin, wmax)
            self.graph.add_edge(ids[i], ids[i + 1], w)

        # Дополнительные рёбра по вероятности
        for i in range(len(ids)):
            for j in range(i + 2, len(ids)):
                if random.random() < prob:
                    w = random.randint(wmin, wmax)
                    self.graph.add_edge(ids[i], ids[j], w)

        self._redraw()
        self._set_status(
            f"Сгенерирован граф: {n} вершин, {len(self.graph.edges)} рёбер.")

    def _validate_for_run(self):
        if len(self.graph.vertices) < 2:
            messagebox.showwarning("Ошибка", "Нужно минимум 2 вершины.")
            return False
        if self.start_vertex is None:
            messagebox.showwarning(
                "Ошибка", "Выберите начальную вершину (режим 'Старт').")
            return False
        if self.end_vertex is None:
            messagebox.showwarning(
                "Ошибка", "Выберите конечную вершину (режим 'Финиш').")
            return False
        if self.start_vertex == self.end_vertex:
            messagebox.showwarning(
                "Ошибка", "Начальная и конечная вершины совпадают.")
            return False
        if self.start_vertex not in self.graph.vertices:
            messagebox.showwarning(
                "Ошибка", "Начальная вершина удалена. Выберите снова.")
            return False
        if self.end_vertex not in self.graph.vertices:
            messagebox.showwarning(
                "Ошибка", "Конечная вершина удалена. Выберите снова.")
            return False
        return True

    def _run_algorithm(self):
        if not self._validate_for_run():
            return

        self._stop_animation()
        self._reset_algo_state()

        dist, prev, order, path = self.graph.dijkstra(
            self.start_vertex, self.end_vertex)

        self._final_dist = dist
        self._final_path = path
        self._final_order = order

        # Готовим шаги анимации
        self._animation_steps = []
        for (u, visited_set) in order:
            self._animation_steps.append({
                "current": u,
                "visited": set(visited_set),
                "path_v": set(),
                "path_e": set(),
            })

        # Финальный шаг — показываем путь
        if path:
            path_v = set(path)
            path_e = set()
            for i in range(len(path) - 1):
                path_e.add((path[i], path[i + 1]))
            self._animation_steps.append({
                "current": None,
                "visited": set(v for v, _ in order),
                "path_v": path_v,
                "path_e": path_e,
            })

        self._anim_index = 0
        self._animate_step()

    def _animate_step(self):
        if self._anim_index >= len(self._animation_steps):
            self._finish_animation()
            return

        step = self._animation_steps[self._anim_index]
        self.current_vertex = step["current"]
        self.visited_vertices = step["visited"]
        self.path_vertices = step["path_v"]
        self.path_edges = step["path_e"]

        if self.current_vertex is not None:
            self._set_status(
                f"Обрабатываем вершину {self.current_vertex}  "
                f"| Посещено: {len(self.visited_vertices)}")
        self._redraw()

        self._anim_index += 1
        self._anim_job = self.root.after(ANIMATION_DELAY, self._animate_step)

    def _finish_animation(self):
        path = self._final_path
        dist = self._final_dist

        if not path:
            self._set_status("Путь не найден!")
            messagebox.showinfo("Результат",
                                f"Путь от вершины {self.start_vertex} "
                                f"до вершины {self.end_vertex} не существует.")
        else:
            total = dist[self.end_vertex]
            path_str = " → ".join(str(v) for v in path)
            self._set_status(
                f"Путь найден! Длина: {total}  |  Маршрут: {path_str}")
            messagebox.showinfo(
                "Кратчайший путь",
                f"Маршрут: {path_str}\n\nДлина пути: {total}")

    def _show_result_instantly(self):
        """Показать конечный результат без анимации."""
        if not self._validate_for_run():
            return
        self._stop_animation()
        self._reset_algo_state()

        dist, prev, order, path = self.graph.dijkstra(
            self.start_vertex, self.end_vertex)

        if path:
            self.path_vertices = set(path)
            self.path_edges = set()
            for i in range(len(path) - 1):
                self.path_edges.add((path[i], path[i + 1]))
            self.visited_vertices = set(v for v, _ in order)
            total = dist[self.end_vertex]
            path_str = " → ".join(str(v) for v in path)
            self._set_status(
                f"Путь найден! Длина: {total}  |  Маршрут: {path_str}")
        else:
            self.visited_vertices = set(v for v, _ in order)
            self._set_status("Путь не найден!")

        self._redraw()

        if not path:
            messagebox.showinfo("Результат",
                                f"Путь от {self.start_vertex} до {self.end_vertex} не найден.")
        else:
            total = dist[self.end_vertex]
            path_str = " → ".join(str(v) for v in path)
            messagebox.showinfo("Кратчайший путь",
                                f"Маршрут: {path_str}\n\nДлина пути: {total}")

    def _reset_algo_state(self):
        self._stop_animation()
        self.current_vertex = None
        self.visited_vertices = set()
        self.path_vertices = set()
        self.path_edges = set()

    def _stop_animation(self):
        if self._anim_job is not None:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None

    def _clear_graph(self):
        self._stop_animation()
        self.graph.clear()
        self.start_vertex = None
        self.end_vertex = None
        self._reset_algo_state()
        self._redraw()
        self._set_status("Граф очищен.")

    def _set_status(self, text):
        self.status_var.set(text)
        self.info_label.config(text=text)


def main():
    root = tk.Tk()
    app = DijkstraApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
