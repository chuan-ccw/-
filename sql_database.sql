create table store
	(store_id		        int,
	 name		    	 	varchar(10),
	 primary key (store_id)
	);


create table order
	(order_id				int,
	 store_id		        int,
	 customer_id  			int,
	 tot_price				int,
	 tot_amount 			int,
	 status 				varchar(10),
	 primary key (order_id)
	 foreign key (store_id) references store (store_id)
	 	on delete set null
	 foreign key (customer_id) references customer (customer_id)
	 	on delete set null	 

	);


create table item
	(item_id				int,
	 order_id				int,
	 product_id				int,
	 size					varchar(10),
	 ice					varchar(10),
	 sugar					varchar(10),
	 temperature			varchar(10),
	 quantity 				int,
	 primary key (item_id)
	 foreign key (order_id) references order (order_id)
	 	on delete set null
	 foreign key (product_id) references product (product_id)
	 	on delete set null	 
	);

create table product
	(product_id				int,
	 name					varchar(10),
	 photo					varchar(255),
	 price					int,
	 primary key (product_id)
	);

create table customer
	(customer_id			int,
	 phone					varchar(10),
	 primary key (customer_id)
	);
