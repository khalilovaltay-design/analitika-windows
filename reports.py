import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from openpyxl import Workbook
from datetime import datetime
import os
import sqlite3

DB_NAME = "pharma.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def reports_window():
    win = tk.Toplevel()
    win.title("Отчёты")
    win.geometry("1100x600")


    # ---------- ФИЛЬТРЫ ----------
    filters = tk.LabelFrame(win, text="Фильтры")
    filters.pack(fill="x", padx=10, pady=5)

    tk.Label(filters, text="Дата с").grid(row=0, column=0, padx=5)
    d1 = DateEntry(filters, date_pattern="dd.MM.yyyy")
    d1.grid(row=0, column=1)

    tk.Label(filters, text="Дата по").grid(row=0, column=2, padx=5)
    d2 = DateEntry(filters, date_pattern="dd.MM.yyyy")
    d2.grid(row=0, column=3)

    tk.Label(filters, text="Регион").grid(row=1, column=0, padx=5)
    e_region = tk.Entry(filters, width=10)
    e_region.grid(row=1, column=1)

    tk.Label(filters, text="Код врача").grid(row=1, column=2, padx=5)
    e_doctor_code = tk.Entry(filters, width=12)
    e_doctor_code.grid(row=1, column=3)

    tk.Label(filters, text="Врач (ФИО)").grid(row=2, column=0, padx=5)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT doctor_code || ' — ' || fio FROM doctors ORDER BY fio")
    doctors_list = [r[0] for r in cur.fetchall()]
    conn.close()

    cb_doctor = ttk.Combobox(filters, values=doctors_list, width=40)
    cb_doctor.grid(row=2, column=1, columnspan=3, sticky="w")
    # ---------- ГРУППИРОВКА ----------
    group = tk.LabelFrame(win, text="Группировка")
    group.pack(fill="x", padx=10, pady=5)

    var_region = tk.BooleanVar(value=True)
    var_doctor = tk.BooleanVar()
    var_product = tk.BooleanVar(value=True)

    tk.Checkbutton(group, text="Регион", variable=var_region).pack(side="left", padx=10)
    tk.Checkbutton(group, text="Врач", variable=var_doctor).pack(side="left", padx=10)
    tk.Checkbutton(group, text="Препарат", variable=var_product).pack(side="left", padx=10)
    # --- фильтр по коду врача ---
    if e_doctor_code.get():
        sql += " AND doctor_code = ?"
        params.append(e_doctor_code.get().strip())

    # --- фильтр по врачу из списка ---
    if cb_doctor.get():
        doctor_code = cb_doctor.get().split(" — ")[0]
        sql += " AND doctor_code = ?"
        params.append(doctor_code)
    # --- ФИЛЬТР ПО ПРЕПАРАТУ ---
    tk.Label(filters, text="Код препарата").grid(row=3, column=0, padx=5)
    e_product_code = tk.Entry(filters, width=15)
    e_product_code.grid(row=3, column=1)

    tk.Label(filters, text="Препарат").grid(row=3, column=2, padx=5)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT product_code || ' — ' || brand
                FROM products
                ORDER BY brand
                """)
    products_list = [r[0] for r in cur.fetchall()]
    conn.close()

    cb_product = ttk.Combobox(filters, values=products_list, width=35)
    cb_product.grid(row=3, column=3, sticky="w")

    # ---------- ТИП ОТЧЁТА ----------
    modes = tk.LabelFrame(win, text="Тип отчёта")
    modes.pack(fill="x", padx=10, pady=5)

    report_mode = tk.StringVar(value="products")

    tk.Radiobutton(modes, text="По продажам",
                   variable=report_mode, value="sales").pack(side="left", padx=10)
    tk.Radiobutton(modes, text="По врачам",
                   variable=report_mode, value="doctors").pack(side="left", padx=10)
    tk.Radiobutton(modes, text="По препаратам",
                   variable=report_mode, value="products").pack(side="left", padx=10)

    # ---------- ТАБЛИЦА ----------
    table_frame = tk.Frame(win)
    table_frame.pack(expand=True, fill="both", padx=10, pady=5)

    tree = ttk.Treeview(table_frame, show="headings")
    tree.pack(expand=True, fill="both")

    # ---------- ИТОГИ ----------
    summary = tk.Frame(win)
    summary.pack(fill="x", padx=10)

    lbl_total = tk.Label(summary, text="Всего: 0")
    lbl_total.pack(side="left", padx=10)

    # ---------- ОСНОВНАЯ ЛОГИКА ----------
    def load():
        tree.delete(*tree.get_children())

        select_fields = []
        group_fields = []
        headers = []

        # --- логика группировки ---
        if var_region.get():
            select_fields.append("region")
            group_fields.append("region")
            headers.append("Регион")

        if report_mode.get() == "doctors" or var_doctor.get():
            select_fields.append("doctor_code")
            group_fields.append("doctor_code")
            headers.append("Врач")

        if report_mode.get() == "products" or var_product.get():
            select_fields.append("product_code")
            group_fields.append("product_code")
            headers.append("Препарат")

        select_fields.append("SUM(quantity)")
        headers.append("Количество")

        sql = f"""
            SELECT {", ".join(select_fields)}
            FROM sales
            WHERE date BETWEEN ? AND ?
        """
        params = [
            d1.get_date().strftime("%Y-%m-%d"),
            d2.get_date().strftime("%Y-%m-%d")
        ]

        if e_region.get():
            sql += " AND region=?"
            params.append(e_region.get())

        if group_fields:
            sql += f" GROUP BY {', '.join(group_fields)}"

        # --- обновляем таблицу ---
        tree["columns"] = headers
        for h in headers:
            tree.heading(h, text=h)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        total = 0
        for r in rows:
            tree.insert("", "end", values=r)
            total += r[-1] or 0

        lbl_total.config(text=f"Всего: {total}")

    def export():
        rows = [tree.item(i)["values"] for i in tree.get_children()]
        if not rows:
            messagebox.showwarning("Экспорт", "Нет данных")
            return

        os.makedirs("exports", exist_ok=True)
        wb = Workbook()
        ws = wb.active
        ws.append(tree["columns"])
        for r in rows:
            ws.append(r)

        fname = f"exports/report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        wb.save(fname)
        messagebox.showinfo("Готово", f"Файл сохранён:\n{fname}")


    # ---------- ИТОГИ ----------
    summary = tk.Frame(win)
    summary.pack(fill="x", padx=10)

    lbl_total = tk.Label(summary, text="Всего продаж: 0")
    lbl_total.pack(side="left", padx=10)

    lbl_rows = tk.Label(summary, text="Строк: 0")
    lbl_rows.pack(side="left", padx=10)

    # ---------- ЛОГИКА ----------
    def load():
        tree.delete(*tree.get_children())

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT product_code, SUM(quantity)
            FROM sales
            WHERE date BETWEEN ? AND ?
            GROUP BY product_code
        """, (
            d1.get_date().strftime("%Y-%m-%d"),
            d2.get_date().strftime("%Y-%m-%d")
        ))

        rows = cur.fetchall()
        conn.close()

        total = 0
        for r in rows:
            tree.insert("", "end", values=r)
            total += r[1] or 0

        lbl_total.config(text=f"Всего продаж: {total}")
        lbl_rows.config(text=f"Строк: {len(rows)}")

    def reset():
        e_region.delete(0, tk.END)
        e_doctor.delete(0, tk.END)
        e_product.delete(0, tk.END)
        var_region.set(False)
        var_doctor.set(False)
        var_product.set(False)
        tree.delete(*tree.get_children())
        lbl_total.config(text="Всего продаж: 0")
        lbl_rows.config(text="Строк: 0")

    def export():
        rows = [tree.item(i)["values"] for i in tree.get_children()]
        if not rows:
            messagebox.showwarning("Экспорт", "Нет данных")
            return

        os.makedirs("exports", exist_ok=True)
        wb = Workbook()
        ws = wb.active
        ws.append(["Препарат", "Количество"])
        for r in rows:
            ws.append(r)

        fname = f"exports/report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        wb.save(fname)
        messagebox.showinfo("Готово", f"Файл сохранён:\n{fname}")

    # ---------- КНОПКИ ----------
    actions = tk.Frame(win)
    actions.pack(pady=10)

    tk.Button(actions, text="Применить", width=15, command=load).pack(side="left", padx=5)
    tk.Button(actions, text="Сброс", width=15, command=reset).pack(side="left", padx=5)
    tk.Button(actions, text="Экспорт", width=18, command=export).pack(side="left", padx=5)


