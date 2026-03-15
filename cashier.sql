CREATE DATABASE CASHIER;

USE CASHIER;

CREATE TABLE Product (
    productId VARCHAR(50) PRIMARY KEY,
    productName VARCHAR(150) NOT NULL,
    price FLOAT NOT NULL,
    stock INT NOT NULL
);
GO
CREATE TABLE Transactions (
    transactionId INT IDENTITY(1,1) PRIMARY KEY,
    transactionDate DATETIME NOT NULL,
    totalPrice FLOAT NOT NULL
);

CREATE TABLE DetailTransaction (
    detailId INT IDENTITY(1,1) PRIMARY KEY, 
    transactionId INT,
    productId VARCHAR(50),
    qty INT NOT NULL,
    subtotal FLOAT NOT NULL,
    FOREIGN KEY (transactionId) REFERENCES Transactions(transactionId),
    FOREIGN KEY (productId) REFERENCES Product(productId)
);
