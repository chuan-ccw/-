USE DrinkShopDB;
GO

DROP TABLE IF EXISTS item;
DROP TABLE IF EXISTS [order];
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS store;

-- 建立門市
CREATE TABLE store
(
    store_id    INT,
    name        NVARCHAR(10),
    PRIMARY KEY (store_id)
);

-- 建立商品
CREATE TABLE product
(
    product_id  INT,
    name        NVARCHAR(10),
    photo_url   NVARCHAR(255),
    price       INT,
    PRIMARY KEY (product_id)
);

-- 建立顧客
CREATE TABLE customer
(
    customer_id INT,
    phone       NVARCHAR(10),
    PRIMARY KEY (customer_id)
)

-- 建立訂單（order 是保留字，要用中括號）
CREATE TABLE [order]
(
    order_id    INT,
    store_id    INT NULL,
    customer_id INT NULL,
    tot_price   INT,
    tot_amount  INT,
    status      NVARCHAR(10),

    PRIMARY KEY (order_id),

    FOREIGN KEY (store_id)
        REFERENCES store(store_id)
        ON DELETE SET NULL,

    FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id)
        ON DELETE SET NULL
);

-- 建立訂單明細 item
CREATE TABLE item
(
    item_id     INT,
    order_id    INT NULL,
    product_id  INT NULL,
    size        NVARCHAR(10),
    ice         NVARCHAR(10),
    sugar       NVARCHAR(10),
    topping     NVARCHAR(10),
    quantity    INT,

    PRIMARY KEY (item_id),

    FOREIGN KEY (order_id)
        REFERENCES [order](order_id)
        ON DELETE SET NULL,

    FOREIGN KEY (product_id)
        REFERENCES product(product_id)
        ON DELETE SET NULL
);

