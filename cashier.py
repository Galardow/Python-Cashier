import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime

class CashierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cashier System")
        self.root.geometry("900x600")
        
        self.db_name = "cashier.db"
        self.initialize_db()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 11), padding=5)
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
        
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        # Menambahkan EditProductFrame ke dalam tuple iterasi
        for F in (LandingFrame, CashierFrame, AddProductFrame, EditProductFrame, UpdateStockFrame, ProductDataFrame, TransactionDataFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame(LandingFrame)
        
    def initialize_db(self):
        queries = [
            """CREATE TABLE IF NOT EXISTS Product (
                productId TEXT PRIMARY KEY,
                productName TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS Transactions (
                transactionId INTEGER PRIMARY KEY AUTOINCREMENT,
                transactionDate TEXT DEFAULT CURRENT_TIMESTAMP,
                totalPrice REAL NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS DetailTransaction (
                detailId INTEGER PRIMARY KEY AUTOINCREMENT,
                transactionId INTEGER,
                productId TEXT,
                qty INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (transactionId) REFERENCES Transactions(transactionId)
            )"""
        ]
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                for q in queries:
                    cursor.execute(q)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error init DB: {e}")

    def show_frame(self, cont):
        frame = self.frames[cont]
        if hasattr(frame, "load_data"): frame.load_data()
        if hasattr(frame, "load_transactions"): frame.load_transactions()
        frame.tkraise()

    def execute_query(self, query, params=(), fetch=False, fetch_all=False):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch:
                    return cursor.fetchall() if fetch_all else cursor.fetchone()
                
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Problem in database :\n{str(e)}")
            return None

class LandingFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)
        ttk.Label(self, text="Cashier Management System", font=("Segoe UI", 20, "bold")).grid(row=0, column=1, pady=20)
        
        # Menambahkan "Edit Product" ke dalam list menu
        menus = [
            ("Cashier", CashierFrame),
            ("Add Product", AddProductFrame),
            ("Edit Product", EditProductFrame),
            ("Update Stock", UpdateStockFrame),
            ("Product Data", ProductDataFrame),    
            ("Transaction Data", TransactionDataFrame) 
        ]
        for i, (text, frame_class) in enumerate(menus, start=1):
            ttk.Button(self, text=text, command=lambda fc=frame_class: controller.show_frame(fc)).grid(row=i, column=1, sticky="ew", padx=200, pady=5)

class CashierFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=20, pady=20)
        
        ttk.Label(input_frame, text="Product ID:").pack(side="left", padx=5)
        self.prod_id_entry = ttk.Entry(input_frame, width=15, font=("Segoe UI", 11))
        self.prod_id_entry.pack(side="left", padx=5)
        
        ttk.Label(input_frame, text="Qty:").pack(side="left", padx=5)
        self.qty_entry = ttk.Entry(input_frame, width=5, font=("Segoe UI", 11))
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(side="left", padx=5)
        
        ttk.Button(input_frame, text="Add to Cart", command=self.add_to_cart).pack(side="left", padx=15)
        
        columns = ("ID", "Name", "Qty", "Price", "Subtotal")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)
        self.tree.pack(fill="both", expand=True, padx=20)
        
        bottom_container = ttk.Frame(self)
        bottom_container.pack(fill="x", padx=20, pady=20)

        button_group = ttk.Frame(bottom_container)
        button_group.pack(side="left")

        ttk.Button(button_group, text="Delete", command=self.remove_selected_item).pack(side="left", padx=2)
        ttk.Button(button_group, text="Clear", command=self.clear_cart).pack(side="left", padx=2)
        ttk.Button(button_group, text="Finish", command=self.finish_transaction).pack(side="left", padx=15)
        ttk.Button(button_group, text="Back", command=lambda: controller.show_frame(LandingFrame)).pack(side="left", padx=2)
        
        self.lbl_total = ttk.Label(bottom_container, text="Total: Rp 0.00", font=("Segoe UI", 16, "bold"))
        self.lbl_total.pack(side="right")

    def add_to_cart(self):
        prod_id = self.prod_id_entry.get().strip()
        qty_str = self.qty_entry.get().strip()
        if not prod_id: return
        try:
            qty = int(qty_str)
            if qty <= 0: raise ValueError
        except: return

        row = self.controller.execute_query("SELECT productName, price, stock FROM Product WHERE productId = ?", (prod_id,), fetch=True)
        if not row:
            messagebox.showerror("Not Found", "Product not found.")
            return
        
        name, price, stock = row
        current_qty_in_cart = sum(int(self.tree.item(c)["values"][2]) for c in self.tree.get_children() if str(self.tree.item(c)["values"][0]) == prod_id)
        
        if (qty + current_qty_in_cart) > stock:
            messagebox.showerror("Stock Error", f"Not enough stock! ({stock})")
            return
            
        self.tree.insert("", "end", values=(prod_id, name, qty, float(price), qty * float(price)))
        self.update_total()

    def remove_selected_item(self):
        for item in self.tree.selection(): self.tree.delete(item)
        self.update_total()

    def clear_cart(self):
        if messagebox.askyesno("Confirm", "Clear all?"):
            for item in self.tree.get_children(): self.tree.delete(item)
            self.update_total()

    def update_total(self):
        total = sum(float(self.tree.item(c)["values"][4]) for c in self.tree.get_children())
        self.lbl_total.config(text=f"Total: Rp {total:,.2f}")
        return total

    def finish_transaction(self):
        if not self.tree.get_children(): return
        total_price = self.update_total()
        
        try:
            with sqlite3.connect(self.controller.db_name) as conn:
                cursor = conn.cursor()
                # Insert Transaction
                cursor.execute("INSERT INTO Transactions(totalPrice) VALUES(?)", (total_price,))
                t_id = cursor.lastrowid
                
                for child in self.tree.get_children():
                    p_id, _, qty, _, sub = self.tree.item(child)["values"]
                    cursor.execute("INSERT INTO DetailTransaction(transactionId, productId, qty, subtotal) VALUES(?,?,?,?)", (t_id, p_id, qty, sub))
                    cursor.execute("UPDATE Product SET stock = stock - ? WHERE productId = ?", (qty, p_id))
                conn.commit()
            
            messagebox.showinfo("Success", "Transaction saved!")
            self.tree.delete(*self.tree.get_children())
            self.update_total()
        except Exception as e:
            messagebox.showerror("Error", str(e))

class AddProductFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        frame = ttk.LabelFrame(self, text="Add new product", padding=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        fields = [("Product ID:", "id"), ("Product Name:", "name"), ("Price:", "price"), ("Stock:", "stock")]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            self.entries[key] = ttk.Entry(frame, width=30)
            self.entries[key].grid(row=i, column=1, pady=5)
        
        ttk.Button(frame, text="Save", command=self.save_product).grid(row=4, column=0, pady=15)
        ttk.Button(frame, text="Back", command=lambda: controller.show_frame(LandingFrame)).grid(row=4, column=1)

    def save_product(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}
        if not all(data.values()): return
        
        query = "INSERT INTO Product(productId, productName, price, stock) VALUES(?,?,?,?)"
        if self.controller.execute_query(query, (data['id'], data['name'], float(data['price']), int(data['stock']))):
            messagebox.showinfo("Success", "Product added!")
            for e in self.entries.values(): e.delete(0, tk.END)

class EditProductFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        top_frame = ttk.Frame(self)
        top_frame.pack(pady=20)
        
        ttk.Label(top_frame, text="Enter Product ID to Edit:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(top_frame, width=20)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(top_frame, text="Search", command=self.load_product).pack(side="left", padx=5)

        self.edit_frame = ttk.LabelFrame(self, text="Edit Product Details", padding=20)
        self.edit_frame.pack(pady=10)
        
        fields = [("New Product ID:", "id"), ("Product Name:", "name"), ("Price:", "price"), ("Stock:", "stock")]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(self.edit_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            self.entries[key] = ttk.Entry(self.edit_frame, width=30)
            self.entries[key].grid(row=i, column=1, pady=5)
            
        self.old_product_id = None

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Update Data", command=self.update_product).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Back", command=lambda: controller.show_frame(LandingFrame)).pack(side="left", padx=10)

    def load_product(self):
        pid = self.search_entry.get().strip()
        if not pid: return
        
        row = self.controller.execute_query("SELECT productId, productName, price, stock FROM Product WHERE productId=?", (pid,), fetch=True)
        if row:
            self.old_product_id = pid
            for e in self.entries.values(): e.delete(0, tk.END)
            self.entries['id'].insert(0, row[0])
            self.entries['name'].insert(0, row[1])
            self.entries['price'].insert(0, row[2])
            self.entries['stock'].insert(0, row[3])
        else:
            messagebox.showerror("Error", "Product ID not found!")

    def update_product(self):
        if not self.old_product_id: 
            messagebox.showwarning("Warning", "Please search for a product first!")
            return
            
        data = {k: v.get().strip() for k, v in self.entries.items()}
        if not all(data.values()): return
        
        query = "UPDATE Product SET productId=?, productName=?, price=?, stock=? WHERE productId=?"
        params = (data['id'], data['name'], float(data['price']), int(data['stock']), self.old_product_id)
        
        if self.controller.execute_query(query, params):
            messagebox.showinfo("Success", "Product successfully updated!")
            self.old_product_id = None
            for e in self.entries.values(): e.delete(0, tk.END)
            self.search_entry.delete(0, tk.END)

class UpdateStockFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        frame = ttk.LabelFrame(self, text="Update Stock", padding=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(frame, text="Product ID:").grid(row=0, column=0)
        self.id_entry = ttk.Entry(frame)
        self.id_entry.grid(row=0, column=1)
        
        ttk.Label(frame, text="Add Qty:").grid(row=1, column=0)
        self.qty_entry = ttk.Entry(frame)
        self.qty_entry.grid(row=1, column=1)
        
        ttk.Button(frame, text="Update", command=self.update_stock).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="Back", command=lambda: controller.show_frame(LandingFrame)).grid(row=3, column=0, columnspan=2)

    def update_stock(self):
        p_id, qty = self.id_entry.get().strip(), self.qty_entry.get().strip()
        if self.controller.execute_query("UPDATE Product SET stock = stock + ? WHERE productId = ?", (int(qty), p_id)):
            messagebox.showinfo("Success", "Updated!")

class ProductDataFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Product Inventory", font=("Segoe UI", 16, "bold")).pack(pady=10)
        cols = ("ID", "Name", "Price", "Stock")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=20)
        ttk.Button(self, text="Back", command=lambda: controller.show_frame(LandingFrame)).pack(pady=10)

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for row in self.controller.execute_query("SELECT * FROM Product", fetch=True, fetch_all=True):
            self.tree.insert("", "end", values=(row[0], row[1], f"Rp {row[2]:,.2f}", row[3]))

class TransactionDataFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Transaction History", font=("Segoe UI", 16, "bold")).pack(pady=5)
        
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="both", expand=True, padx=20)
        
        cols = ("ID", "Time", "Total")
        self.tree = ttk.Treeview(top_frame, columns=cols, show="headings", height=8)
        for c in cols: 
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_transaction_select)

        ttk.Label(self, text="Transaction Details (Click a transaction above)", font=("Segoe UI", 12, "bold")).pack(pady=(15, 5))
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="both", expand=True, padx=20)
        
        detail_cols = ("Product ID", "Product Name", "Qty", "Subtotal")
        self.detail_tree = ttk.Treeview(bottom_frame, columns=detail_cols, show="headings", height=6)
        for c in detail_cols: 
            self.detail_tree.heading(c, text=c)
            self.detail_tree.column(c, anchor="center")
        self.detail_tree.pack(fill="both", expand=True)

        ttk.Button(self, text="Back", command=lambda: controller.show_frame(LandingFrame)).pack(pady=10)

    def load_transactions(self):
        # Bersihkan kedua tabel sebelum memuat ulang
        for i in self.tree.get_children(): self.tree.delete(i)
        for i in self.detail_tree.get_children(): self.detail_tree.delete(i)
        
        for row in self.controller.execute_query("SELECT * FROM Transactions", fetch=True, fetch_all=True):
            self.tree.insert("", "end", values=(row[0], row[1], f"Rp {row[2]:,.2f}"))

    def on_transaction_select(self, event):
        for i in self.detail_tree.get_children(): self.detail_tree.delete(i)
        
        selected_item = self.tree.selection()
        if not selected_item: return
        
        transaction_id = self.tree.item(selected_item[0])["values"][0]
        
        query = """
            SELECT dt.productId, IFNULL(p.productName, 'Unknown/Deleted'), dt.qty, dt.subtotal
            FROM DetailTransaction dt
            LEFT JOIN Product p ON dt.productId = p.productId
            WHERE dt.transactionId = ?
        """
        details = self.controller.execute_query(query, (transaction_id,), fetch=True, fetch_all=True)
        
        if details:
            for row in details:
                self.detail_tree.insert("", "end", values=(row[0], row[1], row[2], f"Rp {row[3]:,.2f}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = CashierApp(root)
    root.mainloop()