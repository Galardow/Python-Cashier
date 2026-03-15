import pyodbc
import tkinter as tk
from tkinter import ttk

DRIVER_NAME = 'SQL SERVER'
SERVER_NAME = 'GALARDO'
DATABASE_NAME = 'CASHIER'

connection_string = f"""
    DRIVER={DRIVER_NAME};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
    Trust_Connection=yes;
"""

root = tk.Tk()

root.title("Cashier")
root.geometry("900x600")

formFrame = tk.Frame(root)
formFrame.pack(fill="both", expand=True) 

formFrame.grid_rowconfigure(0, weight=1)
formFrame.grid_columnconfigure(0, weight=1)

landingFrame = tk.Frame(formFrame)
cashierFrame = tk.Frame(formFrame)
addFrame = tk.Frame(formFrame)
updateFrame = tk.Frame(formFrame)

for frame in (landingFrame, cashierFrame, addFrame, updateFrame):
    frame.grid(row=0, column=0, sticky="nsew")

def show_frame(frame):
    frame.tkraise()

show_frame(landingFrame)

for i in range(2):
    landingFrame.grid_rowconfigure(i, weight=1)
    landingFrame.grid_columnconfigure(i, weight=1)

tk.Button(landingFrame, text="Cashier", font=("Calibri", 14), command=lambda:show_frame(cashierFrame)).grid(row=0, column=1, pady=5)
tk.Button(landingFrame, text="Add Product", font=("Calibri", 14), command=lambda:show_frame(addFrame)).grid(row=1, column=1, pady=5)
tk.Button(landingFrame, text="Update", font=("Calibri", 14), command=lambda:show_frame(updateFrame)).grid(row=2, column=1, pady=5)

for i in range(4):
    cashierFrame.grid_rowconfigure(i, weight=1)
    cashierFrame.grid_columnconfigure(i, weight=1)


tk.Label(cashierFrame, text="Product ID", font=("Calibri", 14)).grid(row=0, column=0, padx=5)
productIdEntry = tk.Entry(cashierFrame, width=15, font=("Calibri", 14))
productIdEntry.grid(row=0, column=1, padx=5, sticky="ew")

tk.Label(cashierFrame, text="Quantity", font=("Calibri", 14)).grid(row=0, column=2, padx=5)
quantityEntry = tk.Entry(cashierFrame, width=5, font=("Calibri", 14))
quantityEntry.grid(row=0, column=3, padx=5, sticky="ew")

cashierColumns = ("Product ID", "Product Name", "Quantity", "Price", "Subtotal")
tree = ttk.Treeview(cashierFrame, columns=cashierColumns, show="headings", height=10)

for col in cashierColumns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center", width=150)
tree.grid(row=1, column=0, columnspan=5, pady=20, sticky="nsew")

def add_to_cart():
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    productId = productIdEntry.get()
    product_name = cursor.execute("""
        SELECT productName
        FROM Product
        WHERE productId = ?
    """, (productId,))
    rowName = cursor.fetchone()
    
    product_name = rowName[0]
    qty = int(quantityEntry.get())
    price = cursor.execute("""
        SELECT price
        FROM Product
        WHERE productId = ?
    """, (productId,))
    rowPrice = cursor.fetchone()
    price = rowPrice[0]
    subtotal = qty * price
    
    tree.insert("", "end", values=(productId, product_name, qty, price, subtotal))
    update_totals()

    conn.commit()

    cursor.close()
    conn.close()

addButton = tk.Button(cashierFrame, text="Add", font=("Calibri", 14), command=add_to_cart)
addButton.grid(row=0, column=4, padx=10)

total_frame = tk.Frame(cashierFrame)
total_frame.grid(row=2, column=0, pady=20, sticky="e")

subtotal_var = tk.StringVar(value="0")
tax_var = tk.StringVar(value="0")
total_var = tk.StringVar(value="0")

tk.Label(total_frame, text="Subtotal:", font=("Calibri", 14)).grid(row=0, column=0)
tk.Label(total_frame, textvariable=subtotal_var, font=("Calibri", 14)).grid(row=0, column=1)

tk.Label(total_frame, text="Tax (10%):", font=("Calibri", 14)).grid(row=1, column=0, padx=5)
tk.Label(total_frame, textvariable=tax_var, font=("Calibri", 14)).grid(row=1, column=1)

tk.Label(total_frame, text="Total:", font=("Calibri", 16, "bold")).grid(row=2, column=0, padx=5)
tk.Label(total_frame, textvariable=total_var, font=("Calibri", 16, "bold")).grid(row=2, column=1)

def update_totals():
    subtotal = 0
    for child in tree.get_children():
        subtotal += float(tree.item(child)["values"][4])
    tax = subtotal * 0.1
    total = subtotal + tax
    subtotal_var.set(f"{subtotal}")
    tax_var.set(f"{tax}")
    total_var.set(f"{total}")

def finish():
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO Transactions(transactionDate, totalPrice)
    OUTPUT INSERTED.transactionId
    VALUES(GETDATE(), ?)
    """, (float(total_var.get()),))

    transactionIdFetch = cursor.fetchone()[0]

    for child in tree.get_children():
        productId, productName, qty, price, subtotal = tree.item(child)["values"]
        
        cursor.execute("""
        INSERT INTO DetailTransaction(transactionId, productId, qty, subtotal)
        VALUES(?, ?, ?, ?)
        """, (transactionIdFetch, productId, qty, subtotal))

        cursor.execute("""
        UPDATE Product
        SET stock = stock - ?
        WHERE productId = ?
        """, (qty, productId))

    conn.commit()

    cursor.close()
    conn.close()

    for child in tree.get_children():
        tree.delete(child)

    subtotal_var.set("0")
    tax_var.set("0")
    total_var.set("0")

finishButton = tk.Button(cashierFrame, text="Finish", font=("Calibri", 14), command=finish)
finishButton.grid(row=3, column=0, columnspan=5, pady=10)

backButton = tk.Button(cashierFrame, text="Back", font=("Calibri", 14), command=lambda:show_frame(landingFrame))
backButton.grid(row=4, column=0, columnspan=5, pady=10)

for i in range(2):
    updateFrame.grid_rowconfigure(i, weight=1)

for i in range(4):
    updateFrame.grid_columnconfigure(i, weight=1)

def update():
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Product
        SET stock = stock + ?
        WHERE productId = ?
    """, (int(stockUpdate.get()), idUpdate.get()))

    stockUpdate.delete(0, tk.END)
    idUpdate.delete(0, tk.END)

    conn.commit()

    cursor.close()
    conn.close()

tk.Label(updateFrame, text="Product id: ", font=("Calibri", 14)).grid(row=0, column=0)
idUpdate = tk.Entry(updateFrame, width=15, font=("Calibri", 14))
idUpdate.grid(row=0, column=1)
tk.Label(updateFrame, text="Stock: ", font=("Calibri", 14)).grid(row=0, column=2)
stockUpdate = tk.Entry(updateFrame, width=15, font=("Calibri", 14))
stockUpdate.grid(row=0, column=3)
tk.Button(updateFrame, text="Update", font=("Calibri", 14), command=update).grid(row=0, column=4)
tk.Button(updateFrame, text="Back", font=("Calibri", 14), command=lambda:show_frame(landingFrame)).grid(row=1, column=2, sticky="ew")

for i in range(1):
    addFrame.grid_columnconfigure(i, weight=1)

for i in range(5):
    addFrame.grid_rowconfigure(i, weight=1)

def add():
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Product(productId, productName, price, stock)
        VALUES(?, ?, ?, ?)
    """, (newProductId.get(), newProductName.get(), float(newProductPrice.get()), int(newProductStock.get())))

    newProductId.delete(0, tk.END)
    newProductName.delete(0, tk.END)
    newProductPrice.delete(0, tk.END)
    newProductStock.delete(0, tk.END)

    conn.commit()

    cursor.close()
    conn.close()

tk.Label(addFrame, text="Product Id: ", font=("Calibri", 14)).grid(row=0, column=0)
newProductId = tk.Entry(addFrame, font=("Calibri", 14))
newProductId.grid(row=0, column=1)
tk.Label(addFrame, text="Product Name: ").grid(row=1, column=0)
newProductName = tk.Entry(addFrame, font=("Calibri", 14))
newProductName.grid(row=1, column=1)
tk.Label(addFrame, text="Price: ").grid(row=2, column=0)
newProductPrice = tk.Entry(addFrame, font=("Calibri", 14))
newProductPrice.grid(row=2, column=1)
tk.Label(addFrame, text="Stock: ").grid(row=3, column=0)
newProductStock = tk.Entry(addFrame, font=("Calibri", 14))
newProductStock.grid(row=3, column=1)
tk.Button(addFrame, text="Add", command=add).grid(row=4, column=1)
tk.Button(addFrame, text="Back", command=lambda:show_frame(landingFrame)).grid(row=5, column=1)

tk.Button(addFrame, text="Back", font=("Calibri", 14), command=lambda:show_frame(landingFrame))

root.mainloop()